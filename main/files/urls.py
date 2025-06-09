from django.urls import path

from .views import ApiFilesView, ApiFileDownloadView, FileDownloadView, FileUploadView

urlpatterns = [
    path("files/upload", FileUploadView.as_view(), name="file-upload"),
    path("files/<str:id>", FileDownloadView.as_view(), name="file-download"),
    path("api/files", ApiFilesView.as_view(), name="api-files"),
    path("api/files/<str:id>", ApiFileDownloadView.as_view(), name="api-file-download"),
]