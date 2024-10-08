from django import forms
from .models import Voter

class SendMessageForm(forms.Form):
    voters = forms.ModelMultipleChoiceField(
        queryset=Voter.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Select Voters"
    )
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}), label="Message")
