from django.urls import path

from .views import ImageUploadView, ApiImagesView

urlpatterns = [
    path("images/upload", ImageUploadView.as_view(), name="image-upload"),
    path("api/images", ApiImagesView.as_view(), name="api-images"),
]