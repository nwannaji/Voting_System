import requests
from django.utils.timezone import now
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.staticfiles import finders
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from django.conf import settings
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

from .formMsg import SendMessageForm
from .models import Candidate, Voter, Position
from django.views.decorators.csrf import csrf_exempt,csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


@csrf_protect  # Ideally, use proper CSRF protection
def voter_login(request):
    if request.method == 'POST':
        unique_id = request.POST.get('unique_id')
        voter_code = request.POST.get('password')
        
        # Authentication logic here
        try:
            voter = Voter.objects.get(unique_id=unique_id, voter_code=voter_code)
            if voter.has_voted:
                messages.info(request, "You have already cast your vote.")
                return redirect('voter_login')
                
            # Store voter ID in session
            request.session['voter_id'] = voter.id
            
            # Redirect to candidate page
            return redirect('candidate_page')  
        except Voter.DoesNotExist:
            messages.error(request, "Invalid login details.")
            return render(request, 'voter_login.html')
    return render(request, 'voter_login.html')

@csrf_exempt
def candidate_page(request):
    if 'voter_id' not in request.session:
        return redirect('voter_login')  # Redirect if not logged in

    if request.method == 'POST':
        selected_ids = request.POST.get('candidates')
        if selected_ids:
            try:
                candidate_ids = [int(id.strip()) for id in selected_ids.split(',')]
            except ValueError:
                messages.error(request, "Invalid candidate IDs.")
                return redirect('candidate_page')

            voted_candidates = []
            for candidate_id in candidate_ids:
                try:
                    candidate = Candidate.objects.get(id=candidate_id)
                    candidate.vote_count += 1
                    candidate.save()
                    voted_candidates.append(candidate.name)
                except Candidate.DoesNotExist:
                    messages.error(request, f"Candidate with ID {candidate_id} not found.")
                    continue

            try:
                voter = Voter.objects.get(id=request.session['voter_id'])
                voter.has_voted = True
                voter.date_voted = now()
                voter.save()
            except Voter.DoesNotExist:
                messages.error(request, "Voter not found.")
                return redirect('voter_login')
            if voter.has_voted:
                messages.info(request, 'You have already cast your vote.')
                return redirect('candidate_page')
                
            if voted_candidates:
                voted_names = ', '.join(voted_candidates)
                messages.success(request, f"You have cast  your vote successfully!")
            else:
                messages.warning(request, "No valid votes were cast.")

            return redirect('candidate_page')

        else:
            messages.error(request, "No candidates were selected.")
            return redirect('candidate_page')

    candidates = Candidate.objects.all()
    return render(request, 'candidate_page.html', {'candidates': candidates})


@csrf_exempt  # Ideally, remove this and use CSRF tokens
def voter_logout(request):
    request.session.flush()  # Clear all session data (logs out the voter)
    return redirect('voter_login')


# Results view
# views.py
def results_view(request):
    positions = Position.objects.all()
    results = {}

    for position in positions:
        # Fetch candidates ordered by vote_count descending
        candidates = Candidate.objects.filter(position=position).order_by('-vote_count')
        
        # Create a dictionary of candidates and their vote counts
        position_result = {candidate.name: candidate.vote_count for candidate in candidates}
        
        # Determine the winner
        if position_result:
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

    # Fetch candidates and their votes for the chart
    all_candidates = Candidate.objects.all()
    for candidate in all_candidates:
        position = candidate.position.name  # Assuming each candidate has a position field
        if position not in positions:
            positions[position] = {}  # Initialize a dictionary for each position
        positions[position][candidate.name] = candidate.vote_count  # Store candidate name and votes

    return render(request, 'chart.html', {'positions': positions})  # Pass 'positions' to the template

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
    organization_name = Paragraph("Government Technical College (GTC) Enugu, Old Boys Association General Elections 2024", title_style)
    
    # Brand logo (assuming it's in the static files directory or specify the path)
    # You can set the logo image size by adjusting the width and height
    logo_path = finders.find('images/nms-logo.png')  # Replace with the actual path to the logo
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
            data.append([idx, position.name, candidate.name, candidate.vote_count])
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
    username = settings.USERNAME
    api_key = settings.API_KEY

    if request.method == 'POST':
        form = SendMessageForm(request.POST)
        if form.is_valid():
            selected_voters = form.cleaned_data['voters']
            # message = form.cleaned_data['message']
            status_messages = []

            for voter in selected_voters:
                phone_number = voter.phone_number
                try:
                    # Generate WhatsApp message content
                    voting_link = generate_voting_link(voter)  # Implement this function as needed
                    message_content = (
                        f"Dear {voter.firstname} {voter.surname},\n"
                        f"Your voting link for the upcoming NMS election is: {voting_link}\n"
                        "You're advised to keep the link secret.\n"
                        f"Your voter login username is your NMS unique identifier, and your password is: {voter.voter_code}."
                    )

                    # Define payload for the WhatsApp message
                    payload = {
                        "WA": {
                            "auth": {
                                "username": username,
                                "apikey": api_key,
                            },
                            "senderID": "NMS Election",
                            "message": {
                                "subject": "Voting Link",
                                "messagetext": message_content,
                            },
                            "recipients": [phone_number],
                        }
                    }

                    # Send the WhatsApp message via eBulkSMS API
                    headers = {"Content-Type": "application/json"}
                    response = requests.post(
                        "https://api.ebulksms.com/sendwhatsapp.json",
                        headers=headers,
                        json=payload
                    )

                    # Handle the response
                    if response.status_code == 200:
                        status_messages.append(f"Message sent to {phone_number} successfully.")
                    else:
                        status_messages.append(f"Failed to send message to {phone_number}: {response.text}")
                except Exception as e:
                    status_messages.append(f"Error sending message to {phone_number}: {str(e)}")

            # Display the status messages on the frontend
            for status in status_messages:
                messages.info(request, status)
            return render(request, 'send_message_status.html', {'status_messages': status_messages})

    else:
        form = SendMessageForm()
       
    return render(request, 'send_whatsApp_msg.html', {'form': form})

def generate_voting_link(voter):
    # Implement your logic to generate the voting link for each voter
    return f"https://nms-elections.com/vote/{voter.unique_id}/"

def send_message_status(request):
    # This view renders the status messages
    status_messages = list(messages.get_messages(request))
    return render(request, 'send_message_status.html', {'status_messages': status_messages})


