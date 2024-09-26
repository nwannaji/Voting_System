from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from .models import Voter

class VoterAuthBackend(BaseBackend):
    """
    Custom authentication backend that authenticates voters using their unique ID and a password
    composed of their surname and phone number.
    """

    def authenticate(self, request, unique_id=None, password=None):
        try:
            voter = Voter.objects.get(unique_id=unique_id)
            # Check if the provided password matches the constructed password
            if voter.password == password:
                return voter  # Authentication successful, return voter object
        except Voter.DoesNotExist:
            return None  # No such voter

    def get_user(self, voter_id):
        try:
            return Voter.objects.get(pk=voter_id)
        except Voter.DoesNotExist:
            return None
