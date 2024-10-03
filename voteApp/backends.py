# voting/backends.py

from django.contrib.auth.backends import ModelBackend
from .models import Voter

class PhoneNumberAuthBackend(ModelBackend):
    def authenticate(self, request, phone_number=None, password=None, **kwargs):
        try:
            user = Voter.objects.get(phone_number=phone_number)
            if user.check_password(password):
                return user
        except Voter.DoesNotExist:
            return None
