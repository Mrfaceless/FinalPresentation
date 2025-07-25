# Generated by Django 5.0.14 on 2025-06-06 04:10

import detector.models
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='CopyrightHolder',
            fields=[
                ('CopyrightHolderID', models.AutoField(primary_key=True, serialize=False)),
                ('Name', models.CharField(max_length=200)),
                ('Role', models.CharField(blank=True, max_length=100)),
                ('Email', models.EmailField(max_length=254, unique=True)),
            ],
            options={
                'db_table': 'CopyrightHolder',
            },
        ),
        migrations.CreateModel(
            name='MusicFile',
            fields=[
                ('MusicFileID', models.AutoField(primary_key=True, serialize=False)),
                ('Title', models.CharField(max_length=200)),
                ('File', models.FileField(upload_to='music_files/')),
                ('UploadDate', models.DateField(auto_now_add=True)),
            ],
            options={
                'db_table': 'MusicFile',
            },
        ),
        migrations.CreateModel(
            name='MusicianProducer',
            fields=[
                ('MusicianID', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('Name', models.CharField(max_length=100)),
                ('Email', models.EmailField(max_length=254, unique=True)),
                ('ContactNumber', models.CharField(blank=True, max_length=20)),
            ],
            options={
                'db_table': 'MusicianProducer',
            },
        ),
        migrations.CreateModel(
            name='CopyrightedMusic',
            fields=[
                ('CopyrightID', models.AutoField(primary_key=True, serialize=False)),
                ('Title', models.CharField(max_length=200)),
                ('AudioFile', models.FileField(upload_to='copyrighted_music/')),
                ('RegistrationDate', models.DateField(validators=[detector.models.validate_not_future])),
                ('Owner', models.CharField(max_length=100)),
                ('CopyrightHolderID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='detector.copyrightholder')),
            ],
            options={
                'db_table': 'CopyrightedMusic',
                'unique_together': {('Title', 'CopyrightHolderID')},
            },
        ),
        migrations.CreateModel(
            name='Analysis',
            fields=[
                ('AnalysisID', models.AutoField(primary_key=True, serialize=False)),
                ('SimilarityScore', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('AnalysisDate', models.DateField(auto_now_add=True)),
                ('CopyrightID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='detector.copyrightedmusic')),
                ('MusicFileID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='detector.musicfile')),
            ],
            options={
                'db_table': 'Analysis',
            },
        ),
        migrations.AddField(
            model_name='musicfile',
            name='MusicianID',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='detector.musicianproducer'),
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('ReportID', models.AutoField(primary_key=True, serialize=False)),
                ('GeneratedDate', models.DateField(auto_now_add=True, validators=[detector.models.validate_not_future])),
                ('Verdict', models.CharField(choices=[('no_violation', 'No Violation'), ('potential_violation', 'Potential Violation'), ('confirmed_violation', 'Confirmed Violation')], max_length=25)),
                ('AnalysisID', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='detector.analysis')),
                ('CopyrightHolderID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='detector.copyrightholder')),
            ],
            options={
                'db_table': 'Report',
            },
        ),
    ]
