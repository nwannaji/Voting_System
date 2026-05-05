import os
import random
import string
from django.db import models
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password

# Position model
class Position(models.Model):
    name = models.CharField(max_length=100)
    display_order = models.IntegerField(default=0, help_text="Lower values display first")

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

# Dynamically generate file path for candidate image uploads
def candidate_image_path(instance, filename):
    return os.path.join(f'candidates/{instance.position.name}', filename)

# Candidate model
class Candidate(models.Model):
    name = models.CharField(max_length=100)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    vote_count = models.IntegerField(default=0)
    photo = models.ImageField(upload_to=candidate_image_path)

    def __str__(self):
        return f"{self.name} ({self.position})"

# Voter model for login using Unique ID and custom password logic
class Voter(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    unique_id = models.CharField(max_length=36, unique=True)  # Unique voter ID
    surname = models.CharField(max_length=100, null=True)
    firstname = models.CharField(max_length=100, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='')
    phone_number = models.CharField(max_length=15, unique=True)  # Unique phone number
    has_voted = models.BooleanField(default=False, db_index=True)
    date_voted = models.DateTimeField(auto_now=True, null=True, blank=True)
    voting_code = models.CharField(max_length=6, unique=True, editable=False)  # Plain 6-char voting code

    class Meta:
        indexes = [
            models.Index(fields=['has_voted']),
            models.Index(fields=['voting_code']),
        ]

    def __str__(self):
        return f"{self.unique_id } {self.surname} {self.firstname}"

    def save(self, *args, **kwargs):
        """
        Overrides the default save method to automatically generate a unique voting_code
        if it hasn't been set already.
        """
        if not self.voting_code:
            self.voting_code = self.generate_unique_voting_code()
        super().save(*args, **kwargs)

    def generate_unique_voting_code(self):
        """
        Generates a unique 6-character alphanumeric voting code.
        Ensures that the generated code does not already exist in the database.
        """
        characters = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choice(characters) for _ in range(6))
            if not Voter.objects.filter(voting_code=code).exists():
                return code

    @staticmethod
    def generate_unique_voting_code_static():
        """Static version for migrations"""
        characters = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choice(characters) for _ in range(6))
            if not Voter.objects.filter(voting_code=code).exists():
                return code

# Ballot model, ties voter to a vote
class Ballot(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE, related_name='ballots')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='ballots')
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='ballots')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = ('voter', 'position')
        indexes = [
            models.Index(fields=['voter', 'position']),
        ]

    def __str__(self):
        return f"Vote by {self.voter.unique_id} for {self.candidate.name} ({self.position})"

# Result model to track votes for each candidate
class Result(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='results')
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='results')
    total_votes = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.candidate.name} - {self.position.name} : {self.total_votes} votes"


























# import os
# from django.db import models
# from django.contrib.auth.models import User

# class Position(models.Model):
#     name = models.CharField(max_length=100)

#     def __str__(self):
#         return self.name
    
# def candidate_image_path(instance, filename):
#     # Construct the file path: 'position_title/filename'
#     return os.path.join(f'candidates/{instance.position.name}', filename)

# class Candidate(models.Model):
#     name = models.CharField(max_length=100)
#     position = models.ForeignKey(Position, on_delete=models.CASCADE)
#     photo = models.ImageField(upload_to=candidate_image_path)  # Dynamically set upload path

#     def __str__(self):
#         return f"{self.name} ({self.position})"


# class Vote(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('user', 'candidate')  # Ensures a user votes only once for a candidate

