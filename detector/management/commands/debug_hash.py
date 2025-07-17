from django.core.management.base import BaseCommand
from detector.models import CopyrightedMusic, AudioFingerprint
from detector.fingerprinting import generate_hashes

class Command(BaseCommand):
    help = 'Compare hashes between uploaded and reference version of the same track'

    def add_arguments(self, parser):
        parser.add_argument('copyright_id', type=int, help='CopyrightedMusicID of the reference track')

    def handle(self, *args, **options):
        copyright_id = options['copyright_id']
        
        try:
            track = CopyrightedMusic.objects.get(pk=copyright_id)
        except CopyrightedMusic.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Track with ID {copyright_id} not found."))
            return

        path = track.AudioFile.path
        generated_hashes = generate_hashes(path)
        generated_hash_set = set(h for h, _ in generated_hashes)
        print(f"Generated {len(generated_hash_set)} hashes from file.")

        # Load DB hashes for the track
        db_hashes = set(
            AudioFingerprint.objects
            .filter(CopyrightedMusicID=track)
            .values_list('Hash', flat=True)
        )
        print(f"Loaded {len(db_hashes)} fingerprints from DB.")

        # Compare overlap
        overlap = generated_hash_set & db_hashes
        print(f"\n[RESULT] Overlapping hashes: {len(overlap)} / {len(generated_hash_set)}")
        print(f"[DEBUG] Overlap percentage: {(len(overlap)/len(generated_hash_set))*100:.2f}%")
