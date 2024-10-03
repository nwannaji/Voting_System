import os
import uuid
from django.db import models
from django.utils.timezone import now
from django.core.validators import RegexValidator
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

# Custom User Manager for Voter
class VoterManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number must be set')
        phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                     message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
        phone_regex(phone_number)
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)

# Position model
class Position(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# Dynamically generate file path for candidate image uploads
def candidate_image_path(instance, filename):
    return os.path.join('candidates', instance.position.name, filename)

# Candidate model
class Candidate(models.Model):
    name = models.CharField(max_length=100)
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='candidates')
    photo = models.ImageField(upload_to=candidate_image_path)

    def __str__(self):
        return f"{self.name} ({self.position.name})"

# Voter model extending Django's AbstractBaseUser
class Voter(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    surname = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    has_voted = models.BooleanField(default=False)
    date_voted = models.DateTimeField(null=True, blank=True)
    voter_code = models.CharField(max_length=6, unique=True, blank=True)

    # Additional required fields for AbstractBaseUser
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # Override groups and user_permissions with unique related_names
    groups = models.ManyToManyField(
        Group,
        related_name='voter_set',  # Changed from default 'user_set' to 'voter_set'
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='voter_set',  # Changed from default 'user_set' to 'voter_set'
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    objects = VoterManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['surname', 'firstname']

    def __str__(self):
        return f"{self.unique_id} - {self.surname} {self.firstname}"

    def save(self, *args, **kwargs):
        if not self.voter_code:
            self.voter_code = self.generate_voter_code()
        super().save(*args, **kwargs)

    def generate_voter_code(self):
        return uuid.uuid4().hex[:6].upper()

# Ballot model, ties voter to a vote
class Ballot(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE, related_name='ballots')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='ballots')
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='ballots')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['voter', 'candidate'], name='unique_vote_per_candidate'),
            models.UniqueConstraint(fields=['voter', 'position'], name='unique_vote_per_position'),
        ]
        
    def save(self, *args, **kwargs):
        if not self.position:
            self.position = self.candidate.position  # Ensure position is set based on candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Vote by {self.voter.unique_id} for {self.candidate.name} ({self.position.name})"

    def __str__(self):
        return f"Vote by {self.voter.unique_id} for {self.candidate.name} ({self.candidate.position.name})"

# Result model to track votes for each candidate
class Result(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='results')
    total_votes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.candidate.name} - {self.candidate.position.name} : {self.total_votes} votes"

    def increment_vote(self):
        self.total_votes += 1
        self.save()

    def decrement_vote(self):
        if self.total_votes > 0:
            self.total_votes -= 1
            self.save()
