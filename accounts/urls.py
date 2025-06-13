from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.register_choice, name='register_choice'),
    path('register/hr/', views.HRRegistrationView.as_view(), name='register_hr'),
    path('register/candidate/', views.CandidateRegistrationView.as_view(), name='register_candidate'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
]
