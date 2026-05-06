# Generated migration for voting link fields

from django.db import migrations, models
import uuid


def generate_unique_tokens(apps, schema_editor):
    """Generate unique tokens for all existing voters."""
    Voter = apps.get_model('votingApp', 'Voter')
    for voter in Voter.objects.all():
        while True:
            new_token = uuid.uuid4()
            # Check if token already exists
            if not Voter.objects.filter(voting_token=new_token).exists():
                voter.voting_token = new_token
                voter.save(update_fields=['voting_token'])
                break


class Migration(migrations.Migration):

    dependencies = [
        ('votingApp', '0015_add_position_display_order'),
    ]

    operations = [
        # First, add the UUID field as nullable without default (no unique constraint)
        migrations.AddField(
            model_name='voter',
            name='voting_token',
            field=models.UUIDField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='voter',
            name='voting_token_expires',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='voter',
            name='voting_link_sent',
            field=models.DateTimeField(null=True, blank=True),
        ),
        # Then populate unique tokens for existing records
        migrations.RunPython(generate_unique_tokens),
        # Finally, set default and make the field unique
        migrations.AlterField(
            model_name='voter',
            name='voting_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True, blank=True),
        ),
    ]
