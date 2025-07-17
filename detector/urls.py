from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_track_view, name='upload_track'),
    path('reports/', views.recent_reports_view, name='recent_reports'),
    path('reports/<int:report_id>/', views.report_detail_view, name='report_detail'),
    path('reports/<int:report_id>/pdf/', views.download_report_pdf, name='report_pdf'),
    path('settings/', views.settings_view, name='settings'),
    path('my-tracks/', views.my_tracks_view, name='my_tracks'),
    path('analytics/', views.musician_analytics_view, name='analytics'),

]