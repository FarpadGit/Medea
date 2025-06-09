from django.urls import path

from .views import ApiImagesView

urlpatterns = [
    path("api/images", ApiImagesView.as_view(), name="api-images"),
]