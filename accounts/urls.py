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
    path('profile/work/add/', views.add_work_experience, name='add_work_experience'),
    path('profile/work/<int:we_id>/edit/', views.edit_work_experience, name='edit_work_experience'),
    path('profile/work/<int:we_id>/delete/', views.delete_work_experience, name='delete_work_experience'),
    path('profile/education/add/', views.add_education, name='add_education'),
    path('profile/education/<int:ed_id>/edit/', views.edit_education, name='edit_education'),
    path('profile/education/<int:ed_id>/delete/', views.delete_education, name='delete_education'),
    path('profile/skill/add/', views.add_skill, name='add_skill'),
    path('profile/skill/<int:skill_id>/delete/', views.delete_skill, name='delete_skill'),
]
