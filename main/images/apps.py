from django.apps import AppConfig
from django.db.backends.signals import connection_created
from django.utils import timezone
from datetime import timedelta
from main.settings import env

class ImagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'images'
    def ready(self):
        connection_created.connect(receiver=cleanup_old_records)
        
# reads database on startup, comment it out if making migrations
def cleanup_old_records(**kwargs):
    from .models import Images, Users, ttl, guest_upload_ttl
    from .utils import start_delete_timer
    from .external_ops import get_images_external, delete_image_external

    temp_records = Images.objects.filter(temporary = True)
    old_records = temp_records.filter(created_at__lt = timezone.now() - timedelta(seconds = ttl)).exclude(uploader__server_side_id = env("MEDEA_GUEST_ID"))
    old_records_for_guest_gallery = temp_records.filter(uploader__server_side_id = env("MEDEA_GUEST_ID"), created_at__lt = timezone.now() - timedelta(seconds = guest_upload_ttl))
    
    for rec in old_records:
        delete_image_external(rec.file_id)
        rec.delete()
    
    for rec in old_records_for_guest_gallery:
        delete_image_external(rec.file_id)
        rec.delete()
    
    # deleting orphan Imagekit images
    WF_images = get_images_external("/wayfarer-uploads")
    for img in WF_images:
        is_img_in_DB = Images.objects.filter(file_id=img.file_id).__len__() > 0
        if not is_img_in_DB:
            delete_image_external(img.file_id)
    
    temp_records = Images.objects.filter(temporary = True)
    for rec in temp_records:
        uploader = Users.objects.get(id=rec.uploader_id)
        ttl_for_current_rec = guest_upload_ttl if uploader.server_side_id == env("MEDEA_GUEST_ID") else ttl
        seconds: int = (rec.created_at + timedelta(seconds = ttl_for_current_rec) - timezone.now()).total_seconds()
        start_delete_timer(seconds, name=rec.name)