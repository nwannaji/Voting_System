from django.contrib import admin
from .models import Candidate, Position, Voter, Ballot, Result


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'vote_count', 'photo')
    list_filter = ('position', 'vote_count')
    search_fields = ('name', 'position__name')
    ordering = ('position__name', 'name')
    readonly_fields = ('vote_count',)

    fieldsets = (
        ('Candidate Information', {
            'fields': ('name', 'position', 'photo')
        }),
        ('Vote Statistics', {
            'fields': ('vote_count',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'surname', 'firstname', 'gender',
                    'phone_number', 'voting_code', 'has_voted', 'date_voted')
    list_filter = ('has_voted', 'gender', 'date_voted')
    search_fields = ('unique_id', 'phone_number', 'surname', 'firstname', 'voting_code')
    readonly_fields = ('date_voted', 'voting_code')
    ordering = ('-date_voted',)

    fieldsets = (
        ('Personal Information', {
            'fields': ('unique_id', 'surname', 'firstname', 'gender', 'phone_number')
        }),
        ('Voting Credentials', {
            'fields': ('voting_code', 'has_voted', 'date_voted'),
            'description': 'Voting code is auto-generated and shown to the voter for login'
        }),
    )


@admin.register(Ballot)
class BallotAdmin(admin.ModelAdmin):
    list_display = ('voter', 'candidate', 'position', 'timestamp')
    list_filter = ('position', 'timestamp')
    search_fields = ('voter__unique_id', 'candidate__name')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'position', 'total_votes')
    list_filter = ('position',)
    search_fields = ('candidate__name',)
    readonly_fields = ('total_votes',)

    fieldsets = (
        ('Election Result', {
            'fields': ('candidate', 'position', 'total_votes')
        }),
    )
