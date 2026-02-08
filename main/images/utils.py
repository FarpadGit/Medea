import string
import random
from .models import Images, Users, ttl
from .external_ops import delete_image_external, update_WF_DB
from threading import Timer
from main.settings import env

def random_string(length=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))

def start_delete_timer(seconds: int = ttl, **kwargs):
    image = Images.objects.get(**kwargs)
    post_id = image.post_id
    uploader_id = image.uploader_id
    timer = Timer(seconds, __delete_image, [post_id, uploader_id, image])
    timer.start()

def __delete_image(post_id: str, uploader_id: str, file: Images):
    print(f"starting image deletion for id {file.file_id} (post id: {post_id}, uploader id: {uploader_id})")
    uploader = Users.objects.get(id=uploader_id)
    delete_image_external(file.file_id)
    file.delete()
    if uploader.server_side_id != env("MEDEA_GUEST_ID"):
        __notify_WF(post_id, uploader.server_side_id, file)
    

def __notify_WF(post_id: str, WF_user_id: str, file: Images):
    update_WF_DB(
        [{
            "name": file.name, 
            "url": "https://placehold.co/600x400?text=Kép%20Törölve%20%2F%20Image%20Deleted", 
            "thumbnailUrl": "https://placehold.co/300x200?text=Kép%20Törölve%20%2F%20Image%20Deleted" }], 
        post_id, 
        WF_user_id)