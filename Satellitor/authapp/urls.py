from django.urls import path
from .views import RegisterView, EmailLoginView, UserProfileView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', EmailLoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),
]