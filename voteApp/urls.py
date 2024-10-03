# voting/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.voter_login, name='login'),
    path('logout/', views.voter_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cast_vote/', views.cast_vote, name='cast_vote'),
    path('results/', views.results, name='results'),
    path('', views.dashboard, name='home'),  # Redirect home to dashboard or login based on authentication
]
