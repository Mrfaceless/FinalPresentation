# --- detector/views.py (core logic examples) ---
from django import forms

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import MusicFile, Report, Analysis,CopyrightedMusic,CopyrightHolder, UserSettings



class MusicUploadForm(forms.ModelForm):
    class Meta:
        model = MusicFile
        fields = ['Title', 'File']

class CopyrightedMusicForm(forms.ModelForm):
    class Meta:
        model = CopyrightedMusic
        fields = ['Title', 'AudioFile', 'RegistrationDate', 'Owner', 'CopyrightHolderID']


@login_required
def dashboard_view(request):
    reports = Report.objects.select_related('analysis', 'analysis__music_file').order_by('-generated_date')[:5]
    return render(request, 'detector/dashboard.html', {'reports': reports})

@login_required
def upload_music_view(request):
    if request.method == 'POST':
        form = MusicUploadForm(request.POST, request.FILES)
        if form.is_valid():
            music_file = form.save(commit=False)
            music_file.musician_producer = request.user.musicianproducer
            music_file.save()
            return redirect('recent_reports')
    else:
        form = MusicUploadForm()
    return render(request, 'detector/upload.html', {'form': form})

@login_required
def recent_reports_view(request):
    reports = Report.objects.select_related('analysis', 'analysis__music_file').order_by('-generated_date')
    return render(request, 'detector/reports.html', {'reports': reports})

@login_required
def report_detail_view(request, report_id):
    report = get_object_or_404(Report.objects.select_related('analysis', 'analysis__music_file', 'analysis__copyrighted_music'), id=report_id)
    return render(request, 'detector/report_detail.html', {'report': report})

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ['report_email', 'notification_pref', 'theme']
        widgets = {
            'report_email': forms.EmailInput(attrs={'placeholder': 'exampleuser@gmail.com'}),
            'notification_pref': forms.Select(),
            'theme': forms.Select(),
        }