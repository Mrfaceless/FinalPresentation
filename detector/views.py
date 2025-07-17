import time
from decimal import Decimal
from collections import Counter
from django.contrib.auth import logout
from .forms import UserSettingsForm
from .models import UserSettings, MusicFile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa
from django.db.models import Count
from django.core.paginator import Paginator

from .fingerprinting import generate_hashes
from .models import (
    MusicFile, MusicianProducer, CopyrightedMusic,
    CopyrightHolder, Analysis, Report, AudioFingerprint
)
from .forms import MusicUploadForm
from .utils.audio_compare import compare_audio


def save_fingerprints(music_file_instance):
    hashes = generate_hashes(music_file_instance.File.path)
    AudioFingerprint.objects.bulk_create([
        AudioFingerprint(MusicFileID=music_file_instance, Hash=h, Offset=offset)
        for h, offset in hashes
    ])


def fingerprint_match(file_path, threshold_ratio=0.003):
    hashes = generate_hashes(file_path)
    if not hashes:
        return None, 0.0, 0

    upload_hash_set = set(h for h, _ in hashes)
    total_hashes = len(upload_hash_set)

    all_fingerprints = AudioFingerprint.objects.filter(CopyrightedMusicID__isnull=False)
    copyright_hash_map = {}
    offset_map = {}

    for fp in all_fingerprints:
        cid = fp.CopyrightedMusicID_id
        if cid not in copyright_hash_map:
            copyright_hash_map[cid] = set()
            offset_map[cid] = []
        copyright_hash_map[cid].add(fp.Hash)
        offset_map[cid].append(fp.Offset)

    best_match_id = None
    best_similarity = 0.0
    best_offset = 0

    for cid, ref_hashes in copyright_hash_map.items():
        matched_hashes = upload_hash_set & ref_hashes
        if not matched_hashes:
            continue

        similarity = len(matched_hashes) / total_hashes
        print(f"[DEBUG] Comparing with CopyrightID={cid}")
        print(f"[DEBUG] Upload hash count: {total_hashes}")
        print(f"[DEBUG] Reference hash count: {len(ref_hashes)}")
        print(f"[DEBUG] Matched hash count: {len(matched_hashes)}")
        print(f"[DEBUG] Manual Similarity: {similarity * 100:.2f}%")

        if similarity > best_similarity:
            best_match_id = cid
            best_similarity = similarity

            offset_diff = []
            for h, u_offset in hashes:
                if h in ref_hashes:
                    ref_offsets = AudioFingerprint.objects.filter(Hash=h, CopyrightedMusicID_id=cid).values_list('Offset', flat=True)
                    for ref_offset in ref_offsets:
                        offset_diff.append(ref_offset - u_offset)
            if offset_diff:
                best_offset = Counter(offset_diff).most_common(1)[0][0]

    if best_match_id and best_similarity >= threshold_ratio:
        try:
            matched_track = CopyrightedMusic.objects.get(pk=best_match_id)
            return matched_track, round(best_similarity * 100, 2), best_offset
        except CopyrightedMusic.DoesNotExist:
            pass

    return None, 0.0, 0


@login_required
def dashboard_view(request):
    return render(request, 'users/dashboard.html')


@login_required
def upload_track_view(request):
    musician_profile, _ = MusicianProducer.objects.get_or_create(
        MusicianID=request.user,
        defaults={'Name': f"{request.user.first_name} {request.user.last_name}".strip(),
                  'Email': request.user.email}
    )

    if request.method == 'POST':
        form = MusicUploadForm(request.POST, request.FILES)
        if form.is_valid():
            music_file = form.save(commit=False)
            music_file.MusicianID = musician_profile
            music_file.save()

            save_fingerprints(music_file)

            best_match, similarity_score, matched_offset = fingerprint_match(music_file.File.path)

            if best_match:
                upload_hashes = generate_hashes(music_file.File.path)
                copyright_hashes = generate_hashes(best_match.AudioFile.path)

                upload_set = set(upload_hashes)
                copyright_set = set(copyright_hashes)

                matched_hashes = upload_set & copyright_set

                print(f"[DEBUG] Upload hash count: {len(upload_set)}")
                print(f"[DEBUG] Reference hash count: {len(copyright_set)}")
                print(f"[DEBUG] Matched hash count: {len(matched_hashes)}")
                similarity_score = (len(matched_hashes) / len(upload_set)) * 100
                print(f"[DEBUG] Manual Similarity: {(len(matched_hashes) / len(upload_set)) * 100:.2f}%")

            if not best_match:
                similarity_score = 0.0
                matched_offset = 0
                for ref in CopyrightedMusic.objects.exclude(AudioFile="").all():
                    try:
                        score = compare_audio(music_file.File.path, ref.AudioFile.path)
                        if score > similarity_score:
                            similarity_score = score
                            best_match = ref
                    except Exception:
                        continue

            if not best_match:
                dummy_holder, _ = CopyrightHolder.objects.get_or_create(
                    Name="Dummy Holder", Email="dummy@example.com"
                )
                best_match = CopyrightedMusic.objects.create(
                    Title="Dummy Reference Track",
                    Owner="System",
                    RegistrationDate="2023-01-01",
                    AudioFile="",
                    CopyrightHolderID=dummy_holder
                )
            print(f"[DEBUG] Saving similarity to DB: {similarity_score:.2f}%")
            analysis = Analysis.objects.create(
                MusicFileID=music_file,
                CopyrightID=best_match,
                SimilarityScore=Decimal(str(round(similarity_score, 2))),
                MatchedOffset=matched_offset
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
                CopyrightHolderID=best_match.CopyrightHolderID,
                CopyrightID=best_match
            )

            messages.success(request, f"Track analyzed. Similarity: {similarity_score:.2f}% — {verdict.replace('_', ' ').title()}")
            return redirect('recent_reports')
    else:
        form = MusicUploadForm()

    reports = (
        Report.objects
        .filter(AnalysisID__MusicFileID__MusicianID=musician_profile)
        .select_related('AnalysisID')
        .order_by('-ReportID')[:5]
    )

    return render(request, 'detector/upload.html', {'form': form, 'reports': reports})


@login_required
def recent_reports_view(request):
    files = MusicFile.objects.filter(MusicianID__MusicianID=request.user)

    all_reports = (
        Report.objects
        .filter(AnalysisID__MusicFileID__in=files)
        .select_related('AnalysisID')
        .order_by('-ReportID')
    )

    paginator = Paginator(all_reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'detector/reports.html', {'reports': page_obj})


@login_required
def report_detail_view(request, report_id):
    report = get_object_or_404(
        Report.objects.select_related(
            'AnalysisID', 'AnalysisID__MusicFileID', 'AnalysisID__CopyrightID'),
        ReportID=report_id,
        AnalysisID__MusicFileID__MusicianID__MusicianID=request.user
    )
    AudioFingerprint.objects.filter(MusicFileID=report.AnalysisID.MusicFileID).delete()
    return render(request, 'detector/report_detail.html', {
        'report': report,
        'matched_offset': report.AnalysisID.MatchedOffset or 0
    })


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
def my_tracks_view(request):
    musician = get_object_or_404(MusicianProducer, MusicianID=request.user)

    if request.method == 'POST':
        track_id = request.POST.get('delete_track_id')
        if track_id:
            try:
                track = MusicFile.objects.get(MusicFileID=track_id, MusicianID=musician)
                track.File.delete()
                track.delete()
                messages.success(request, f"Track '{track.Title}' deleted successfully.")
                return redirect('my_tracks')
            except MusicFile.DoesNotExist:
                messages.error(request, "Track not found or not authorized to delete.")

    tracks = MusicFile.objects.filter(MusicianID=musician)
    return render(request, 'detector/my_tracks.html', {'tracks': tracks})


@login_required
def settings_view(request):
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'delete_account':
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, "Your account has been deleted.")
            return redirect('home')

        elif action == 'delete_tracks':
            MusicFile.objects.filter(MusicianID__MusicianID=request.user).delete()
            messages.success(request, "All your uploaded tracks have been deleted.")
            return redirect('settings')

        else:
            form = UserSettingsForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, "Settings updated successfully.")
                return redirect('settings')
    else:
        form = UserSettingsForm(instance=settings_obj)

    return render(request, 'detector/settings.html', {'form': form})

@login_required
def musician_analytics_view(request):
    musician = get_object_or_404(MusicianProducer, MusicianID=request.user)

    # Total uploaded tracks
    total_tracks = MusicFile.objects.filter(MusicianID=musician).count()

    # Total analyses
    total_analyses = Analysis.objects.filter(MusicFileID__MusicianID=musician).count()

    # Verdict breakdown
    verdicts = Report.objects.filter(
        AnalysisID__MusicFileID__MusicianID=musician
    ).values('Verdict').annotate(count=Count('Verdict'))

    verdict_counts = {
        'no_violation': 0,
        'potential_violation': 0,
        'confirmed_violation': 0
    }

    for v in verdicts:
        verdict_counts[v['Verdict']] = v['count']

    # Recent similarity scores (optional)
    recent_scores = Analysis.objects.filter(
        MusicFileID__MusicianID=musician
    ).order_by('-AnalysisDate')[:5]

    return render(request, 'detector/analytics.html', {
        'total_tracks': total_tracks,
        'total_analyses': total_analyses,
        'verdict_counts': verdict_counts,
        'recent_scores': recent_scores
    })
