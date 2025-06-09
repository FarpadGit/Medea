import uuid
from django.db import models

ttl = int(30 * 24 * 60 * 60)
max_upload_size = 10 * 1024 * 1024

class Files(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    download_id = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    def __str__(self):
        return self.name