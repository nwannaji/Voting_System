# voting/backends.py

import logging
from django.contrib.auth.backends import ModelBackend
from .models import Voter

logger = logging.getLogger('voteApp')

class PhoneNumberAuthBackend(ModelBackend):
    def authenticate(self, request, phone_number=None, password=None, **kwargs):
        try:
            user = Voter.objects.get(phone_number=phone_number)
            if user.check_password(password):
                logger.info(f"Authentication successful for voter: {user.unique_id}")
                return user
            else:
                logger.warning(f"Authentication failed - wrong password for phone: {phone_number}")
        except Voter.DoesNotExist:
            logger.warning(f"Authentication failed - voter not found for phone: {phone_number}")
        return None
