from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Upload files from the local media/ folder to the configured default storage (e.g. Supabase Storage)."

    def add_arguments(self, parser):
        parser.add_argument('--overwrite', action='store_true', help="Re-upload files that already exist remotely.")

    def handle(self, *args, overwrite=False, **options):
        if 'S3' not in settings.STORAGES['default']['BACKEND']:
            raise CommandError("MEDIA_BUCKET is not set, so default storage is the local disk. Set the MEDIA_* variables first.")

        root = Path(settings.MEDIA_ROOT)
        uploaded = skipped = 0
        for path in sorted(p for p in root.rglob('*') if p.is_file()):
            name = path.relative_to(root).as_posix()
            if default_storage.exists(name):
                if not overwrite:
                    skipped += 1
                    continue
                default_storage.delete(name)
            with path.open('rb') as fh:
                saved = default_storage.save(name, File(fh))
            if saved != name:
                self.stdout.write(self.style.WARNING(f"  {name} was stored as {saved}"))
            uploaded += 1
            self.stdout.write(f"  uploaded {name}")
        self.stdout.write(self.style.SUCCESS(f"Done: {uploaded} uploaded, {skipped} already present."))
