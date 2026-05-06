from django import forms
from .models import Candidate

class VoteForm(forms.Form):
    candidates = forms.ModelMultipleChoiceField(
        queryset=Candidate.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

class VoterRegForm(forms.Form):
    unique_id = forms.CharField(max_length=50, required=True, label='NMS Unique ID')
    surname = forms.CharField(max_length=100, required=True,label='Surname')
    firstname = forms.CharField(max_length=100, required=True, label='First Name')


class VoterLoginForm(forms.Form):
    phone_number = forms.CharField(max_length=15, required=True, label='Phone Number')
    voter_code = forms.CharField(max_length=6, required=True, label='Password', widget=forms.PasswordInput)  
