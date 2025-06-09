import random
import string
from rest_framework.request import Request, HttpRequest
from .models import Files, ttl

from threading import Timer

def generate_random_string(length):
    random_string = "".join(random.choices(string.ascii_letters + string.digits, k=length))
    return random_string

def generate_database_entry(name: str, content: str):
    download_id = generate_random_string(6)
    while Files.objects.filter(download_id = download_id).count() > 0:
        download_id = generate_random_string(6)
    
    # convert decrypted data into an HttpRequest body for Django Rest Framework to use and save into db
    save_request = Request(HttpRequest())
    save_request._full_data = { 
        "name": name,
        "content": content,
        "download_id": download_id
    }

    return save_request, download_id

# start a timer to delete newly added record "TTL" seconds from upload
def start_delete_timer(download_id: str, seconds: int = ttl):
    new_file = Files.objects.get(download_id = download_id)
    timer = Timer(seconds, lambda file: file.delete(), [new_file])
    timer.start()