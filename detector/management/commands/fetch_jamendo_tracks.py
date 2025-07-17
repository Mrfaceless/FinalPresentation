import os
import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from detector.models import CopyrightedMusic, CopyrightHolder
from django.utils import timezone
from datetime import datetime
from random import randint
JAMENDO_API_URL = "https://api.jamendo.com/v3.0/tracks/"
JAMENDO_CLIENT_ID = "aff732b8"  # Replace with your actual Jamendo API client ID

class Command(BaseCommand):
    help = "Fetch and store random Jamendo tracks into the database"




    def handle(self, *args, **kwargs):
        self.stdout.write("Fetching random tracks from Jamendo...")

        params = {
    "client_id": JAMENDO_CLIENT_ID,
    "format": "json",
    "limit": 20,
    "audioformat": "mp32",
    "random": "true",
    "offset": randint(10, 10000)  # random offset each time
}

        response = requests.get(JAMENDO_API_URL, params=params)
        if response.status_code != 200:
            self.stderr.write(f"Failed to fetch data from Jamendo. Status code: {response.status_code}")
            return

        tracks = response.json().get("results", [])
        self.stdout.write(f"Found {len(tracks)} tracks.")

        for track in tracks:
            title = track.get("name")
            artist = track.get("artist_name")
            download_url = track.get("audio")
            if not title or not artist or not download_url:
                continue

            # Create or get the copyright holder
            holder, _ = CopyrightHolder.objects.get_or_create(
                Name=artist,
                defaults={
                    "Email": f"{artist.replace(' ', '').lower()}@jamendo.com"
                }
            )

            # Download the file content
            try:
                audio_response = requests.get(download_url)
                if audio_response.status_code != 200:
                    self.stderr.write(f"Failed to download audio for {title}")
                    continue

                audio_file = ContentFile(audio_response.content)
                file_name = f"{title.replace(' ', '_')}_{artist.replace(' ', '_')}.mp3"

                # Create copyrighted music entry
                music = CopyrightedMusic(
                    Title=title,
                    Owner=artist,
                    RegistrationDate=timezone.now().date(),
                    CopyrightHolderID=holder
                )
                music.AudioFile.save(file_name, audio_file)
                music.save()

                self.stdout.write(f"Saved: {title} by {artist}")

            except Exception as e:
                self.stderr.write(f"Error saving {title}: {str(e)}")
