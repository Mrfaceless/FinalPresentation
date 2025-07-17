from django.urls import path
from .views import signup_view
from detector.views import dashboard_view


urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('dashboard/', dashboard_view, name='dashboard'),
]

