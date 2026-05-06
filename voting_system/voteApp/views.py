# views.py

import os
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction
from .models import Position, Candidate, Ballot, Result, Voter

# Optional: Import logging if you wish to log errors
import logging

logger = logging.getLogger(__name__)

def voter_login(request):
    """
    Handles voter login using phone number and password.
    """
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        
        # Authenticate the voter
        user = authenticate(request, phone_number=phone_number, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Successfully logged in.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid phone number or password.')
    
    return render(request, 'voting/login.html')


@login_required
def voter_logout(request):
    """
    Logs out the authenticated voter.
    """
    logout(request)
    messages.success(request, 'Successfully logged out.')
    return redirect('login')


@login_required
def dashboard(request):
    """
    Displays all positions and their respective candidates.
    Indicates which positions the voter has already voted for.
    """
    positions = Position.objects.prefetch_related('candidates').all()
    voter = request.user
    
    # Retrieve positions the voter has already voted for
    voted_positions = Ballot.objects.filter(voter=voter).values_list('candidate__position__id', flat=True)
    
    context = {
        'positions': positions,
        'voted_positions': voted_positions,
    }
    
    return render(request, 'voting/dashboard.html', context)


@login_required
@require_POST
def cast_vote(request):
    """
    Handles the voting process.
    Ensures that a voter can only vote once per position.
    """
    voter = request.user
    candidate_id = request.POST.get('candidate_id')
    
    # Validate the candidate ID
    candidate = get_object_or_404(Candidate, id=candidate_id)
    position = candidate.position
    
    # Check if the voter has already voted for this position
    has_voted = Ballot.objects.filter(voter=voter, candidate__position=position).exists()
    
    if has_voted:
        messages.error(request, f'You have already voted for the position of {position.name}.')
        return redirect('dashboard')
    
    try:
        with transaction.atomic():
            # Create a new ballot
            Ballot.objects.create(voter=voter, candidate=candidate, position=position)
            
            # Optionally, update the voter's has_voted and date_voted fields
            # Note: If voting per position, consider removing has_voted from Voter model
            voter.has_voted = True
            voter.date_voted = timezone.now()
            voter.save()
            
            messages.success(request, f'Your vote for {candidate.name} has been successfully cast.')
    
    except Exception as e:
        messages.error(request, 'An error occurred while casting your vote. Please try again.')
        logger.error(f"Error casting vote: {e}")
    
    return redirect('dashboard')


def results(request):
    """
    Displays the current voting results.
    Shows total votes each candidate has received per position.
    """
    positions = Position.objects.prefetch_related('candidates__results').all()
    
    context = {
        'positions': positions,
    }
    
    return render(request, 'voting/results.html', context)
