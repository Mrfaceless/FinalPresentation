from django.contrib import admin
from django.contrib.auth.models import User
from .models import (
    MusicianProducer, MusicFile, CopyrightHolder,
    CopyrightedMusic, Analysis, Report
)

# --------------------
# Inline classes
# --------------------

class MusicFileInline(admin.TabularInline):
    model = MusicFile
    extra = 1

class CopyrightedMusicInline(admin.TabularInline):
    model = CopyrightedMusic
    extra = 1

class AnalysisInline(admin.TabularInline):
    model = Analysis
    extra = 1

class ReportInline(admin.TabularInline):
    model = Report
    extra = 1


# --------------------
# Admin classes
# --------------------

@admin.register(MusicianProducer)
class MusicianProducerAdmin(admin.ModelAdmin):
    list_display = ('MusicianID', 'Name', 'Email', 'ContactNumber')
    search_fields = ('Name', 'Email')
    inlines = [MusicFileInline]

@admin.register(MusicFile)
class MusicFileAdmin(admin.ModelAdmin):
    list_display = ('MusicFileID', 'Title', 'UploadDate', 'MusicianID')
    list_filter = ('UploadDate',)
    search_fields = ('Title',)

@admin.register(CopyrightHolder)
class CopyrightHolderAdmin(admin.ModelAdmin):
    list_display = ('CopyrightHolderID', 'Name', 'Role', 'Email')
    search_fields = ('Name', 'Email')
    inlines = [CopyrightedMusicInline]

@admin.register(CopyrightedMusic)
class CopyrightedMusicAdmin(admin.ModelAdmin):
    list_display = ('CopyrightID', 'Title', 'Owner', 'RegistrationDate', 'CopyrightHolderID')
    list_filter = ('RegistrationDate',)
    search_fields = ('Title',)
    inlines = [AnalysisInline]

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ('AnalysisID', 'MusicFileID', 'CopyrightID', 'SimilarityScore', 'AnalysisDate')
    list_filter = ('AnalysisDate',)
    search_fields = ('MusicFileID__Title',)
    inlines = [ReportInline]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'ReportID', 'AnalysisID', 'Verdict', 'GeneratedDate',
        'CopyrightHolderID', 'CopyrightID'
    )
    list_filter = ('Verdict', 'GeneratedDate')
    search_fields = ('Verdict',)
    change_list_template = "admin/report_changelist.html"  # <- custom template

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        total_reports = Report.objects.count()
        no_violation = Report.objects.filter(Verdict='no_violation').count()
        potential_violation = Report.objects.filter(Verdict='potential_violation').count()
        confirmed_violation = Report.objects.filter(Verdict='confirmed_violation').count()
        total_users = User.objects.count()
        total_tracks = MusicFile.objects.count()

        extra_context['summary'] = {
            'Total Reports': total_reports,
            'No Violation': no_violation,
            'Potential Violation': potential_violation,
            'Confirmed Violation': confirmed_violation,
        }
        extra_context['total_users'] = total_users
        extra_context['total_tracks'] = total_tracks

        return super().changelist_view(request, extra_context=extra_context)
