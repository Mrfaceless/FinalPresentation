# core/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='dashboard', permanent=False)),
    path('home/', RedirectView.as_view(pattern_name='dashboard', permanent=False), name='home'),
    path('users/', include('users.urls')),       # Handles signup/login
    path('accounts/', include('django.contrib.auth.urls')),  # Login/logout
    path('detector/', include('detector.urls')),  # Main app for music detection
]

# Serve uploaded media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
