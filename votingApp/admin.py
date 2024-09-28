from django.contrib import admin
from .models import Candidate, Position,Voter

    
class VoterAdmin(admin.ModelAdmin):
    fieldsets = [
        ('VoterDetails',{'fields':[ 'unique_id','surname','firstname','gender','phone_number',
                                            'has_voted','date_voted','voter_code']}),
        ]
    
    list_display =('unique_id','surname','firstname','gender','phone_number',
                   'has_voted','date_voted','voter_code',)
    
    readonly_fields =('date_voted',)

admin.site.register(Candidate)
admin.site.register(Position)
admin.site.register(Voter, VoterAdmin)
# admin.site.register(Ballot)
# admin.site.register(Result)
