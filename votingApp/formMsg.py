from django import forms
from .models import Voter

class SendMessageForm(forms.Form):
    voters = forms.ModelMultipleChoiceField(
        queryset=Voter.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Select Voters"
    )
