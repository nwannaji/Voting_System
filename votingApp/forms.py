from django import forms
from .models import Candidate

class VoteForm(forms.Form):
    candidates = forms.ModelMultipleChoiceField(
        queryset=Candidate.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # This allows multiple selections in the form
        required=False
    )

class VoterRegForm(forms.Form):
    unique_id = forms.CharField(max_length=50, required=True, label='NMS Unique ID')
    surname = forms.CharField(max_length=100, required=True,label='Surname')
    firstname = forms.CharField(max_length=100, required=True, label='First Name')
    
    
class VoterLoginForm(forms.Form):
    unique_id = forms.CharField(max_length=100, label='Unique ID')
    voter_code = forms.CharField(max_length=6, required=True,label='Password', widget=forms.PasswordInput)  # The password will be a combination of surname and phone number
