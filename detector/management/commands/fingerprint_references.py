# detector/scripts/fingerprint_reference_tracks.py

from django.core.management.base import BaseCommand
from detector.models import CopyrightedMusic, AudioFingerprint
from detector.fingerprinting import generate_hashes

class Command(BaseCommand):
    help = 'Generate fingerprints for all reference (copyrighted) tracks.'

    def handle(self, *args, **options):
        tracks = CopyrightedMusic.objects.exclude(AudioFile="")

        if not tracks.exists():
            self.stdout.write(self.style.WARNING("No reference tracks found."))
            return

        self.stdout.write(f"Found {tracks.count()} reference track(s).")

        choice = input(
            "\nChoose an option:\n"
            "  [1] Delete all existing reference fingerprints and regenerate\n"
            "  [2] Only generate missing fingerprints (skip already fingerprinted)\n"
            "Enter 1 or 2: "
        ).strip()

        if choice == '1':
            self.stdout.write(self.style.WARNING("Deleting all existing reference fingerprints..."))
            deleted = AudioFingerprint.objects.filter(CopyrightedMusicID__isnull=False).delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {deleted[0]} fingerprints."))

        elif choice != '2':
            self.stdout.write(self.style.ERROR("Invalid option. Aborting."))
            return

        count = 0
        for track in tracks:
            try:
                if choice == '2' and AudioFingerprint.objects.filter(CopyrightedMusicID=track).exists():
                    self.stdout.write(self.style.NOTICE(f"Skipping {track.Title} (already fingerprinted)"))
                    continue

                path = track.AudioFile.path
                hashes = generate_hashes(path)

                if not hashes:
                    self.stdout.write(self.style.WARNING(f"⚠ No hashes generated for {track.Title}"))
                    continue

                fingerprints = [
                    AudioFingerprint(
                        Hash=h,
                        Offset=offset,
                        CopyrightedMusicID=track
                    )
                    for h, offset in hashes
                ]

                AudioFingerprint.objects.bulk_create(fingerprints)
                self.stdout.write(self.style.SUCCESS(f"✓ Fingerprinted: {track.Title} ({len(hashes)} hashes)"))
                count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error on {track.Title}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\nDone. Fingerprinted {count} new track(s)."))
