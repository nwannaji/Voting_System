from django import forms
from .models import Voter


class SendMessageForm(forms.Form):
    voters = forms.ModelMultipleChoiceField(
        queryset=Voter.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Select Voters"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable voters who have already received a WhatsApp message
        for voter in self.fields['voters'].queryset:
            if voter.voting_link_sent:
                # This disables the checkbox for already-messaged voters
                pass  # We'll handle this in the template

    def clean_voters(self):
        voters = self.cleaned_data['voters']
        # Filter out voters who have already received a message
        return [v for v in voters if not v.voting_link_sent]
