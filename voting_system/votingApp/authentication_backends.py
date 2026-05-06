from django.contrib.auth.backends import BaseBackend
from .models import Voter

class VoterAuthBackend(BaseBackend):

    def authenticate(self, request, phone_number=None, password=None):
        try:
            voter = Voter.objects.get(phone_number=phone_number)
            # Simple comparison for plain text voting_code
            if password == voter.voting_code:
                return voter  # Authentication successful, return voter object
        except Voter.DoesNotExist:
            return None  # No such voter

    def get_user(self, voter_id):
        try:
            return Voter.objects.get(pk=voter_id)
        except Voter.DoesNotExist:
            return None
