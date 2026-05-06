import hmac
import logging
import requests
from django.utils.timezone import now
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.staticfiles import finders
from django.core.cache import cache
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from django.conf import settings
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from django.db import models, transaction, IntegrityError
from .formMsg import SendMessageForm
from .models import Candidate, Voter, Position, Ballot, Result
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import F

logger = logging.getLogger('votingApp')


@csrf_protect
def voter_login(request):
    show_message = request.session.pop('show_already_voted_message', False)
    client_ip = request.META.get('REMOTE_ADDR', 'unknown')

    # Rate limiting: block after 5 failed attempts in 15 minutes
    login_attempts = cache.get(f'login_attempts_{client_ip}', 0)
    if login_attempts >= 5:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        messages.error(request, "Too many login attempts. Please try again in 15 minutes.")
        return render(request, 'voter_login.html', {'show_already_voted_message': show_message})

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        password = request.POST.get('password', '').strip()

        # Input validation and sanitization
        if not phone_number or len(phone_number) > 15:
            logger.warning(f"Invalid phone number length from IP: {client_ip}")
            messages.error(request, "Invalid phone number.")
            return render(request, 'voter_login.html')

        if not password or len(password) > 50:
            logger.warning(f"Invalid password length from IP: {client_ip}")
            messages.error(request, "Invalid password.")
            return render(request, 'voter_login.html')

        # Authentication logic using phone number
        try:
            voter = Voter.objects.get(phone_number=phone_number)
            if hmac.compare_digest(voter.voting_code, password):
                cache.delete(f'login_attempts_{client_ip}')  # Reset on success
                logger.info(f"Successful login for voter: {voter.unique_id} from IP: {client_ip}")
                if voter.has_voted:
                    request.session['show_already_voted_message'] = True
                    return redirect('voter_login')

                request.session['voter_id'] = voter.id
                return redirect('candidate_page')
        except Voter.DoesNotExist:
            pass

        # Increment failed attempts
        cache.set(f'login_attempts_{client_ip}', login_attempts + 1, timeout=900)
        logger.warning(f"Failed login attempt for phone: {phone_number} from IP: {client_ip}")
        messages.error(request, "Invalid login details.")
        return render(request, 'voter_login.html')

    return render(request, 'voter_login.html', {'show_already_voted_message': show_message})


def vote_with_link(request, token):
    """View to handle voting via unique link."""
    client_ip = request.META.get('REMOTE_ADDR', 'unknown')

    try:
        voter = Voter.objects.get(voting_token=token)

        # Check if link is expired
        if not voter.is_voting_link_valid():
            logger.warning(f"Expired voting link used: token {token} from IP: {client_ip}")
            messages.error(request, "This voting link has expired. Please request a new link.")
            return render(request, 'link_expired.html')

        # Check if already voted
        if voter.has_voted:
            logger.info(f"Double vote attempt via link by voter: {voter.unique_id}")
            messages.info(request, "You have already cast your vote.")
            return redirect('results')

        # Set session and proceed to voting
        request.session['voter_id'] = voter.id
        request.session['link_authenticated'] = True
        logger.info(f"Voter authenticated via link: {voter.unique_id}")
        return redirect('candidate_page')

    except Voter.DoesNotExist:
        logger.warning(f"Invalid voting link used: token {token} from IP: {client_ip}")
        messages.error(request, "Invalid voting link.")
        return render(request, 'invalid_link.html')


def candidate_page(request):
    if 'voter_id' not in request.session:
        return redirect('voter_login')

    if request.method == 'POST':
        selected_ids = request.POST.get('candidates')
        if selected_ids:
            # Limit input length and sanitize
            selected_ids = selected_ids.strip()[:500]
            # Validate format (only numbers and commas)
            if not all(c.isdigit() or c == ',' for c in selected_ids):
                logger.warning(f"Malformed candidate IDs submitted: {selected_ids[:100]}")
                messages.error(request, "Invalid candidate selection.")
                return redirect('candidate_page')

            try:
                candidate_ids = [int(id.strip())
                                 for id in selected_ids.split(',') if id.strip()]
                # Limit number of candidates
                if len(candidate_ids) > 20:
                    logger.warning(f"Too many candidates selected: {len(candidate_ids)}")
                    messages.error(request, "Too many candidates selected.")
                    return redirect('candidate_page')
            except ValueError:
                logger.warning(f"Invalid candidate IDs submitted: {selected_ids}")
                messages.error(request, "Invalid candidate IDs.")
                return redirect('candidate_page')

            voted_candidates = []
            voter = None

            try:
                voter = Voter.objects.get(id=request.session['voter_id'])
                if voter.has_voted:
                    logger.warning(f"Double vote attempt by voter: {voter.unique_id}")
                    messages.info(request, 'You have already cast your vote.')
                    return redirect('candidate_page')
            except Voter.DoesNotExist:
                logger.error(f"Voter not found for session: {request.session.get('voter_id')}")
                messages.error(request, "Voter not found.")
                return redirect('voter_login')

            voted_candidates = []

            # Process each candidate vote in its own atomic block
            for candidate_id in candidate_ids:
                try:
                    with transaction.atomic():
                        candidate = Candidate.objects.get(id=candidate_id)

                        # Check if voter already voted for this position
                        if Ballot.objects.filter(voter=voter, position=candidate.position).exists():
                            logger.warning(f"Duplicate vote for position {candidate.position.name} by voter {voter.unique_id}")
                            messages.error(request, f"You have already voted for {candidate.position.name}.")
                            continue

                        # Create ballot record
                        Ballot.objects.create(
                            voter=voter,
                            candidate=candidate,
                            position=candidate.position
                        )

                        # Update vote count using F() to prevent race conditions
                        Candidate.objects.filter(id=candidate_id).update(
                            vote_count=models.F('vote_count') + 1)

                        # Get the updated vote count
                        candidate.refresh_from_db()

                        # Update or create Result record
                        Result.objects.update_or_create(
                            candidate=candidate,
                            position=candidate.position,
                            defaults={'total_votes': candidate.vote_count}
                        )

                        voted_candidates.append(candidate.name)
                        logger.info(f"Vote cast by {voter.unique_id} for candidate {candidate.name}")

                except Candidate.DoesNotExist:
                    logger.warning(f"Candidate not found: ID {candidate_id}")
                    messages.error(request, f"Candidate with ID {candidate_id} not found.")
                    continue

            # Mark voter as voted if at least one vote was cast
            if voted_candidates:
                with transaction.atomic():
                    voter.has_voted = True
                    voter.date_voted = now()
                    voter.save(update_fields=['has_voted', 'date_voted'])
                voter.save()
                logger.info(f"Vote cast successfully by voter: {voter.unique_id} for candidates: {voted_candidates}")

            if voted_candidates:
                messages.success(
                    request, f"You have cast your vote successfully!")
            else:
                messages.warning(request, "No valid votes were cast.")

            return redirect('candidate_page')

        else:
            messages.error(request, "No candidates were selected.")
            return redirect('candidate_page')

    # Group candidates by position in Python for predictable ordering
    positions = Position.objects.all().order_by('display_order', 'name')
    candidates_by_position = {}
    for pos in positions:
        candidates_by_position[pos] = list(
            Candidate.objects.filter(position=pos).order_by('name'))

    return render(request, 'candidate_page.html', {
        'candidates_by_position': candidates_by_position
    })


@csrf_protect  # Ideally, remove this and use CSRF tokens
def voter_logout(request):
    request.session.flush()  # Clear all session data (logs out the voter)
    return redirect('voter_login')


# Results view
# views.py
def results_view(request):
    positions = Position.objects.all().order_by('display_order', 'name')
    results = {}

    for position in positions:
        # Fetch candidates ordered by vote_count descending
        candidates = list(Candidate.objects.filter(
            position=position).order_by('-vote_count'))

        # Create a dictionary of candidates and their vote counts
        position_result = {
            candidate.name: candidate.vote_count for candidate in candidates}

        # Determine the winner - check for tie (multiple candidates with same max votes)
        if position_result:
            max_votes = max(position_result.values())
            candidates_with_max = [name for name, votes in position_result.items() if votes == max_votes]
            if len(candidates_with_max) > 1:
                # There's a tie - no clear winner
                winner_name, winner_votes = "No winner emerged", None
            else:
                winner_name, winner_votes = next(iter(position_result.items()))
        else:
            winner_name, winner_votes = None, None

        # Store candidates and winner in the results dictionary
        results[position.name] = {
            'candidates': position_result,
            'winner': {
                'name': winner_name,
                'votes': winner_votes
            }
        }
    return render(request, 'results.html', {'results': results})


# Chart view
def chart_view(request):
    positions = {}  # Create a dictionary to hold positions and their candidates

    # Fetch candidates and their votes for the chart, ordered by position display_order
    all_candidates = Candidate.objects.select_related('position').all().order_by('position__display_order', 'position__name')
    for candidate in all_candidates:
        position = candidate.position.name  # Assuming each candidate has a position field
        if position not in positions:
            # Initialize a dictionary for each position
            positions[position] = {}
        # Store candidate name and votes
        positions[position][candidate.name] = candidate.vote_count

    # Pass 'positions' to the template
    return render(request, 'chart.html', {'positions': positions})


def export_results_to_pdf(request):
    # Create HTTP response with appropriate content type for PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="voting_results.pdf"'

    # Create a PDF document and specify the page size
    pdf = SimpleDocTemplate(response, pagesize=A4)

    # Sample styles for the document (used for organization name and title)
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.alignment = TA_CENTER
    normal_style = styles['Normal']

    # Organization title (Name of the organization)
    organization_name = Paragraph(
        "Nigerian Bar Association Abuja Branch<br/>General Elections 2026", title_style)

    # Brand logo (assuming it's in the static files directory or specify the path)
    # You can set the logo image size by adjusting the width and height
    # Replace with the actual path to the logo
    logo_path = finders.find('images/nba.jpg')
    if logo_path:
        logo = Image(logo_path)
        logo.drawHeight = 1.25 * inch
        logo.drawWidth = 1.25 * inch
    else:
        logo = Paragraph('Logo not found', normal_style)

    # Add some space between the logo, organization name, and the table
    spacer = Spacer(1, 0.25 * inch)

    # Prepare the data to be included in the table
    data = [["#", "Position", "Candidate", "Vote Count"]]
    positions = Position.objects.all()

    row_number = 1
    for position in positions:
        candidates = Candidate.objects.filter(position=position)
        for idx, candidate in enumerate(candidates, start=1):
            data.append(
                [idx, position.name, candidate.name, candidate.vote_count])
            row_number += 1

    # Create a table with the data
    table = Table(data)

    # Add style to the table (like borders, background colors)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    # Build the PDF document by adding the logo, title, spacer, and table
    pdf.build([logo, organization_name, spacer, table])
    return response


@csrf_protect  # Use proper CSRF protection
def send_voter_whatsApp_message(request):
    ebulk_username = settings.EBULKSMS_USERNAME
    ebulk_api_key = settings.EBULKSMS_API_KEY
    at_username = settings.AFRICAS_TALKING_USERNAME
    at_api_key = settings.AFRICAS_TALKING_API_KEY
    at_wa_number = settings.AFRICAS_TALKING_WA_NUMBER

    # Check if coming from admin action with pre-selected voters
    selected_voter_ids = request.session.get('selected_voter_ids', [])

    if request.method == 'POST':
        form = SendMessageForm(request.POST)
        if form.is_valid():
            selected_voters = form.cleaned_data['voters']
            status_messages = []

            for voter in selected_voters:
                phone_number = voter.phone_number
                try:
                    # Generate WhatsApp message content
                    voting_link = generate_voting_link(voter)
                    message_content = (
                        f"Dear {voter.firstname} {voter.surname},\n\n"
                        f"You have been registered to vote in the NBA Abuja Branch Elections 2026.\n\n"
                        f"Click the link below to cast your vote:\n"
                        f"{voting_link}\n\n"
                        f"This link is personal and expires in 7 days. Please keep it confidential.\n\n"
                        f"Best regards,\n"
                        f"NBA Abuja Branch Election Committee"
                    )

                    # Try eBulkSMS first
                    success = False
                    error_msg = None

                    # Try eBulkSMS
                    payload = {
                        "WA": {
                            "auth": {
                                "username": ebulk_username,
                                "apikey": ebulk_api_key,
                            },
                            "senderID": "NBAiDecide",
                            "message": {
                                "subject": "NBA Abuja Branch - Voting Link",
                                "messagetext": message_content,
                            },
                            "recipients": [phone_number],
                        }
                    }

                    try:
                        headers = {"Content-Type": "application/json"}
                        response = requests.post(
                            "https://api.ebulksms.com/sendwhatsapp.json",
                            headers=headers,
                            json=payload,
                            timeout=30
                        )

                        if response.status_code == 200:
                            success = True
                            logger.info(f"WhatsApp message sent via eBulkSMS to {phone_number}")
                    except Exception as e:
                        error_msg = str(e)
                        logger.warning(f"eBulkSMS failed for {phone_number}: {e}")

                    # If eBulkSMS failed, try Africa's Talking
                    if not success and at_api_key:
                        try:
                            at_payload = {
                                "username": at_username,
                                "waNumber": at_wa_number,
                                "phoneNumber": phone_number,
                                "body": {
                                    "message": message_content
                                }
                            }

                            headers = {
                                "apikey": at_api_key,
                                "content-type": "application/json"
                            }

                            at_response = requests.post(
                                "https://chat.africastalking.com/whatsapp/message/send",
                                headers=headers,
                                json=at_payload,
                                timeout=30
                            )

                            if at_response.status_code == 200 or at_response.status_code == 201:
                                success = True
                                logger.info(f"WhatsApp message sent via Africa's Talking to {phone_number}")
                            else:
                                error_msg = f"Africa's Talking: {at_response.text}"

                        except Exception as e:
                            error_msg = f"Africa's Talking failed: {str(e)}"
                            logger.error(f"Africa's Talking error for {phone_number}: {e}")

                    # Handle result
                    if success:
                        status_messages.append(f"Message sent to {phone_number} successfully.")
                    else:
                        status_messages.append(f"Failed to send message to {phone_number}: {error_msg}")

                except Exception as e:
                    logger.error(f"Error sending message to {phone_number}: {str(e)}")
                    status_messages.append(f"Error sending message to {phone_number}: {str(e)}")

            # Display the status messages on the frontend
            for status in status_messages:
                messages.info(request, status)
            return render(request, 'send_message_status.html', {'status_messages': status_messages})

    else:
        form = SendMessageForm()

        # Pre-select voters if coming from admin action (filter out already messaged)
        if selected_voter_ids:
            form.fields['voters'].queryset = Voter.objects.filter(
                id__in=selected_voter_ids,
                voting_link_sent__isnull=True
            )
            # Clear the session
            request.session.pop('selected_voter_ids', None)
            request.session.pop('send_to_all', None)
        else:
            # By default, only show voters who haven't received WhatsApp messages
            form.fields['voters'].queryset = Voter.objects.filter(voting_link_sent__isnull=True)

    return render(request, 'send_whatsApp_msg.html', {'form': form})


def generate_voting_link(voter):
    """Generate a unique voting link using the voter's voting token."""
    base_url = getattr(settings, 'BASE_URL', 'https://your-azure-app.azurewebsites.net')
    return voter.generate_voting_link(base_url)


def send_message_status(request):
    # This view renders the status messages
    status_messages = list(messages.get_messages(request))
    return render(request, 'send_message_status.html', {'status_messages': status_messages})
