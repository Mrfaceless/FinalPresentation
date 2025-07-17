# detector/views.py
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa

from .models import (
    MusicFile, MusicianProducer, CopyrightedMusic,
    CopyrightHolder, Analysis, Report
)
from .forms import MusicUploadForm

@login_required
def dashboard_view(request):
    return render(request, 'users/dashboard.html')

@login_required
def upload_track_view(request):
    # Create or fetch MusicianProducer profile
    musician_profile, _ = MusicianProducer.objects.get_or_create(
        MusicianID=request.user,
        defaults={
            'Name': f"{request.user.first_name} {request.user.last_name}".strip(),
            'Email': request.user.email
        }
    )

    if request.method == 'POST':
        form = MusicUploadForm(request.POST, request.FILES)
        if form.is_valid():
            music_file = form.save(commit=False)
            music_file.MusicianID = musician_profile
            music_file.save()

            similarity_score = round(random.uniform(0, 100), 2)

            ref_music = CopyrightedMusic.objects.first()
            if not ref_music:
                dummy_holder, _ = CopyrightHolder.objects.get_or_create(
                    Name="Dummy Holder", Email="dummy@example.com"
                )
                ref_music = CopyrightedMusic.objects.create(
                    Title="Dummy Reference Track",
                    Owner="System",
                    RegistrationDate="2023-01-01",
                    AudioFile="",
                    CopyrightHolderID=dummy_holder
                )

            analysis = Analysis.objects.create(
                MusicFileID=music_file,
                CopyrightID=ref_music,
                SimilarityScore=similarity_score
            )

            verdict = (
                "no_violation" if similarity_score < 30 else
                "potential_violation" if similarity_score < 70 else
                "confirmed_violation"
            )

            Report.objects.create(
                AnalysisID=analysis,
                GeneratedDate=timezone.now().date(),
                Verdict=verdict,
                CopyrightHolderID=ref_music.CopyrightHolderID
            )

            messages.success(
                request,
                f"Track analyzed. Similarity: {similarity_score}% — {verdict.replace('_', ' ').title()}"
            )
            return redirect('recent_reports')
    else:
        form = MusicUploadForm()

    reports = Report.objects.filter(
        AnalysisID__MusicFileID__MusicianID=musician_profile
    ).select_related('AnalysisID')

    return render(request, 'detector/upload.html', {
        'form': form,
        'reports': reports
    })


@login_required
def recent_reports_view(request):
    files = MusicFile.objects.filter(MusicianID__MusicianID=request.user)
    reports = Report.objects.filter(AnalysisID__MusicFileID__in=files).select_related('AnalysisID')
    return render(request, 'detector/reports.html', {'reports': reports})


@login_required
def report_detail_view(request, report_id):
    report = get_object_or_404(
        Report.objects.select_related('AnalysisID', 'AnalysisID__MusicFileID', 'AnalysisID__CopyrightID'),
        ReportID=report_id,
        AnalysisID__MusicFileID__MusicianID__MusicianID=request.user
    )
    return render(request, 'detector/report_detail.html', {'report': report})


@login_required
def download_report_pdf(request, report_id):
    report = get_object_or_404(
        Report,
        ReportID=report_id,
        AnalysisID__MusicFileID__MusicianID__MusicianID=request.user
    )
    template_path = 'detector/report_pdf.html'
    context = {'report': report}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{report.ReportID}.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('PDF generation failed', status=500)
    return response


@login_required
def settings_view(request):
    return render(request, 'detector/settings.html')
