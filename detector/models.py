from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

# --- Custom Validators ---
def validate_not_future(value):
    if value > timezone.now().date():
        raise ValidationError("Date cannot be in the future.")

# --- Models ---

class MusicianProducer(models.Model):
    MusicianID = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    Name = models.CharField(max_length=100)
    Email = models.EmailField(unique=True)
    ContactNumber = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.Name

    class Meta:
        db_table = 'MusicianProducer'


class MusicFile(models.Model):
    MusicFileID = models.AutoField(primary_key=True)
    Title = models.CharField(max_length=200)
    File = models.FileField(upload_to='music_files/')
    UploadDate = models.DateField(auto_now_add=True)
    MusicianID = models.ForeignKey(MusicianProducer, on_delete=models.CASCADE)

    def __str__(self):
        return self.Title

    class Meta:
        db_table = 'MusicFile'

class CopyrightHolder(models.Model):
    CopyrightHolderID = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=200)
    Role = models.CharField(max_length=100, blank=True)
    Email = models.EmailField(unique=True)

    def __str__(self):
        return self.Name

    class Meta:
        db_table = 'CopyrightHolder'


class CopyrightedMusic(models.Model):
    CopyrightID = models.AutoField(primary_key=True)
    Title = models.CharField(max_length=200)
    AudioFile = models.FileField(upload_to='copyrighted_music/')
    RegistrationDate = models.DateField(validators=[validate_not_future])
    Owner = models.CharField(max_length=100)
    CopyrightHolderID = models.ForeignKey(CopyrightHolder, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("Title", "CopyrightHolderID")
        db_table = 'CopyrightedMusic'

    def __str__(self):
        return self.Title


class Analysis(models.Model):
    AnalysisID = models.AutoField(primary_key=True)
    MusicFileID = models.ForeignKey(MusicFile, on_delete=models.CASCADE)
    CopyrightID = models.ForeignKey(CopyrightedMusic, on_delete=models.CASCADE)
    SimilarityScore = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    MatchedOffset = models.FloatField(null=True, blank=True)
    AnalysisDate = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Analysis {self.AnalysisID}"

    class Meta:
        db_table = 'Analysis'


class Report(models.Model):
    ReportID = models.AutoField(primary_key=True)
    AnalysisID = models.OneToOneField(Analysis, on_delete=models.CASCADE)
    GeneratedDate = models.DateField(auto_now_add=True, validators=[validate_not_future])
    Verdict = models.CharField(max_length=25, choices=[
        ('no_violation', 'No Violation'),
        ('potential_violation', 'Potential Violation'),
        ('confirmed_violation', 'Confirmed Violation')
    ])
    CopyrightHolderID = models.ForeignKey(CopyrightHolder, on_delete=models.CASCADE)

    #NEW FIELD
    CopyrightID = models.ForeignKey(CopyrightedMusic, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Report {self.ReportID}: {self.get_Verdict_display()}"

    class Meta:
        db_table = 'Report'
        
class AudioFingerprint(models.Model):
    FingerprintID = models.AutoField(primary_key=True)
    MusicFileID = models.ForeignKey('MusicFile', on_delete=models.CASCADE, null=True, blank=True)
    CopyrightedMusicID = models.ForeignKey('CopyrightedMusic', on_delete=models.CASCADE, null=True, blank=True)
    Hash = models.CharField(max_length=255)
    Offset = models.IntegerField()

    class Meta:
        indexes = [
            models.Index(fields=['Hash']),
            models.Index(fields=['Hash', 'MusicFileID']),  # ← Optional but strongly recommended
            models.Index(fields=['Hash', 'CopyrightedMusicID'])
        ]
class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    report_email = models.EmailField(blank=True, null=True)

    NOTIFY_CHOICES = [
        ('all', 'All Notifications'),
        ('important', 'Only Important'),
        ('none', 'None'),
    ]
    notification_pref = models.CharField(max_length=20, choices=NOTIFY_CHOICES, default='all')

    THEME_CHOICES = [
        ('system', 'System Theme'),
        ('light', 'Light Theme'),
        ('dark', 'Dark Theme'),
    ]
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='system')

    def __str__(self):
        return f"{self.user.username}'s Settings"

    class Meta:
        db_table = 'UserSettings'
