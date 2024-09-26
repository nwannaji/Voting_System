from django import forms
from .models import Candidate

class VoteForm(forms.Form):
    candidates = forms.ModelMultipleChoiceField(
        queryset=Candidate.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # This allows multiple selections in the form
        required=False
    )
    
class VoterLoginForm(forms.Form):
    unique_id = forms.CharField(max_length=100, label='Unique ID')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')  # The password will be a combination of surname and phone number
