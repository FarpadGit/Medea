import base64
import json
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, Http404
from django.shortcuts import render, get_object_or_404
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response

from .models import Files, max_upload_size
from .serializers import FilesSerializer
from .encryption import decrypt
from .utils import generate_database_entry, start_delete_timer

class ApiFilesView(ListCreateAPIView):
    queryset = Files.objects.all()
    serializer_class = FilesSerializer
    lookup_field = "name"
    lookup_url_kwarg = "id"

    def get(self, request, *args, **kwargs):
        return Response(data={ "count": Files.objects.count() })

    def post(self, request, *args, **kwargs):
        # decrypt incoming data
        if "ac" not in request.data or "origin" not in request.data: 
            return HttpResponseBadRequest()
        encrypted_payload = bytearray(request.data["ac"], "utf-8")
        origin = request.data["origin"]

        decrypted_data = decrypt(encrypted_payload)

        match origin:
            case "CM":
                save_request, download_id = generate_database_entry("Clandescent Moon Playlist", decrypted_data)
                response = super().post(save_request, *args, **kwargs)
                start_delete_timer(download_id)

                del response.data["id"]
                return response
            case _: return HttpResponseBadRequest("Incorrect origin")

        

class ApiFileDownloadView(RetrieveAPIView):
    queryset = Files.objects.all()
    serializer_class = FilesSerializer
    lookup_field = "download_id"
    lookup_url_kwarg = "id"

    def get(self, request, *args, **kwargs):
        try:
            response = super().get(request, *args, **kwargs)
        except Http404:
            response = HttpResponseNotFound(json.dumps({ "error": "No such file in database" }))
            response.headers["Content-Type"] = "application/json"
            return response
        
        file = Files.objects.get(download_id = response.data["download_id"])
        file.delete()
        return response

class FileDownloadView(ListCreateAPIView):
    serializer_class = FilesSerializer

    def get(self, request, *args, **kwargs):
        context = {}
        file = get_object_or_404(Files, download_id = kwargs["id"])

        context["name"] = file.name
        context["download_id"] = file.download_id
        context["created_at"] = file.created_at
        context["content"] = file.content
            
        return render(request, "download.html", context)

    def post(self, request, *args, **kwargs):
        if "filename" not in request.data or "content" not in request.data:
            raise Http404()
        
        decoded_content = base64.b64decode(request.data["content"])
    
        response = HttpResponse(decoded_content, content_type="application/octet-stream")
        response["Content-Disposition"] = f"attachment; filename={request.data['filename']}"

        try:
            file = get_object_or_404(Files, download_id = kwargs["id"])
            file.delete()
        except:
            return render(request, '404.html')

        return response
    
class FileUploadView(ListCreateAPIView):
    serializer_class = FilesSerializer

    context = {}
    context["max_size"] = max_upload_size

    def get(self, request, *args, **kwargs):
        return render(request, "file_upload.html", self.context)

    def post(self, request, *args, **kwargs):
        if "file" not in request.data or "file" not in request.FILES:
            return render(request, "file_upload.html", self.context)
        
        filename = str(request.data["file"]).replace("-", "_")
        file = request.FILES["file"]

        if file.size > max_upload_size:
            context = { **self.context, "error_msg": "File too large" }
            return render(request, "file_upload.html", context)
        
        binary = file.read(max_upload_size)
        
        save_request, download_id = generate_database_entry(filename, base64.b64encode(binary).decode())
        super().post(save_request, *args, **kwargs)
        start_delete_timer(download_id)

        context = { **self.context, "download_id": download_id, "host": request.get_host() }
        return render(request, "file_upload.html", context)