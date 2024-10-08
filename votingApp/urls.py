from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .import views

urlpatterns = [
    path('', views.voter_login, name='voter_login'), #Voter login page
    path('candidates/', views.candidate_page, name='candidate_page'), #Voting page
    path('logout/', views.voter_logout, name='voter_logout'), #Voter logout page
    path('results/', views.results_view, name='results'), #Results page
    path('chart/', views.chart_view, name='chart'),
    path('export-results/', views.export_results_to_pdf, name='export_results'),
    path('sendMessage/',views.send_voter_whatsApp_message, name='sendMessage'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
