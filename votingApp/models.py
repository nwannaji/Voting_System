import os
from django.db import models
from django.utils.timezone import now

# Position model remains the same
class Position(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# Dynamically generate file path for candidate image uploads
def candidate_image_path(instance, filename):
    return os.path.join(f'candidates/{instance.position.name}', filename)

# Candidate model remains the same
class Candidate(models.Model):
    name = models.CharField(max_length=100)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    vote_count =models.IntegerField(default=0)
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
    has_voted = models.BooleanField(default=False)
    date_voted = models.DateTimeField(default=now,null=True, blank=True)
    voter_code = models.CharField(max_length=6, unique=True, blank=True)  # Alphanumeric voter code


    def __str__(self):
        return f"{self.unique_id} - {self.surname}"

    @property
    def password(self):
        # Combine surname and phone number as password
         f"{self.surname}{self.unique_id}"

# Ballot model remains the same, ties voter to a vote
class Ballot(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('voter', 'position')

    def __str__(self):
        return f"Vote by {self.voter.unique_id} for {self.candidate.name} ({self.position})"

# Result model to track votes for each candidate
class Result(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
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

