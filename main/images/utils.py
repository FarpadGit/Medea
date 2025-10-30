import string
import random
from .models import Images, ttl
from .external_ops import delete_image_external, update_WF_DB
from threading import Timer

def random_string(length=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))

def start_delete_timer(seconds: int = ttl, **kwargs):
    new_image = Images.objects.get(**kwargs)
    post_id = new_image.post_id
    uploader_id = new_image.uploader_id
    timer = Timer(seconds, __delete_and_notify_WF, [post_id, uploader_id, new_image])
    timer.start()

def __delete_and_notify_WF(post_id: str, uploader_id: str, file: Images):
    filename = file.name
    file_id = file.file_id
    file.delete()
    delete_image_external(file_id)
    update_WF_DB(
        [{ 
            "name": filename, 
            "url": "https://placehold.co/600x400?text=Kép%20Törölve%20%2F%20Image%20Deleted", 
            "thumbnailUrl": "https://placehold.co/300x200?text=Kép%20Törölve%20%2F%20Image%20Deleted" }], 
        post_id, 
        uploader_id)