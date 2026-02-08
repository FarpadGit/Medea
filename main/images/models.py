import uuid
import datetime
from django.db import models

ttl = int(30 * 24 * 60 * 60)
guest_upload_ttl = int(1 * 24 * 60 * 60)
max_upload_size = 2.5 * 1024 * 1024

class Images(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    file_id = models.CharField(max_length=100, unique=True)
    url = models.CharField(max_length=200)
    thumbnail_url = models.CharField(max_length=200)
    post_id = models.CharField(max_length=100, blank=True)
    uploader = models.ForeignKey("Users", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    temporary = models.BooleanField(default=True)

    @property
    def deleted_at_guest(self):
        return  self.created_at + datetime.timedelta(seconds=guest_upload_ttl)
    
    @property
    def deleted_at(self):
        return  self.created_at + datetime.timedelta(seconds=ttl)

    def __str__(self):
        return self.name

class Users(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    server_side_id = models.CharField(max_length=100)
    slug = models.CharField(max_length=100)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name