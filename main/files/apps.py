from django.apps import AppConfig
from django.db.backends.signals import connection_created
from django.utils import timezone
from datetime import timedelta

class FilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'files'
    def ready(self):
        connection_created.connect(receiver=cleanup_old_records)
        
# reads database on startup, comment it out if making migrations
def cleanup_old_records(**kwargs):
    from .models import Files, ttl
    from .utils import start_delete_timer

    old_records = Files.objects.filter(created_at__lt = timezone.now() - timedelta(seconds = ttl))
    for rec in old_records:
        rec.delete()
    
    for rec in Files.objects.all():
        seconds: int = (rec.created_at + timedelta(seconds = ttl) - timezone.now()).total_seconds()
        start_delete_timer(rec.download_id, seconds)