import re
import magic
from django.views.generic import ListView
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from rest_framework.generics import ListCreateAPIView, DestroyAPIView
from rest_framework.request import Request, HttpRequest
from rest_framework.response import Response
from django.shortcuts import render

from main.settings import env
from .models import Users, Images, ttl, guest_upload_ttl, max_upload_size
from .serializers import ImagesSerializer
from .encryption import decrypt
from .external_ops import upload_image_external, delete_image_external, update_WF_DB
from .utils import start_delete_timer, random_string

import vercel_blob

class HomePageView(ListView):
    model = Images
    template_name = "home.html"

class ApiImagesView(ListCreateAPIView, DestroyAPIView):
    queryset = Images.objects.all()
    serializer_class = ImagesSerializer
    imageName = ""

    # used by super.delete()
    def get_object(self):
        return Images.objects.get(name=self.imageName)

    def post(self, request, *args, **kwargs):
        payload = request.data

        # decrypt incoming data
        if "ac" not in payload or "origin" not in payload: 
            return HttpResponseBadRequest("Incorrect payload")
        
        encrypted_payload = bytearray(payload["ac"], "utf-8")
        origin = payload["origin"]

        decrypted_data = decrypt(encrypted_payload)

        match origin:
            case "WF":
                required_fields = "files", "post_id", "uploader_id", "uploader_name"
                for field in required_fields:
                    if field not in decrypted_data: return HttpResponseBadRequest(f"Incorrect payload, '{field}' field is required")

                for file in decrypted_data["files"]:
                    if "name" not in file or "url" not in file: return HttpResponseBadRequest("Incorrect payload, 'files' field should be an array of 'name' and 'url'")

                # upload images stored in Vercel Blob to external storage and clear them from blob storage
                uploaded_images = upload_image_external(decrypted_data["files"], decrypted_data["folder"] if "folder" in decrypted_data else "/")
                for blobfile in decrypted_data["files"]:
                    vercel_blob.delete(blobfile["url"])
                
                image_names = []

                for image in uploaded_images:
                    image_names.append({"name": image["name"], "url": image["url"], "thumbnailUrl": image["thumbnail"]})

                    user_in_DB = Users.objects.filter(server_side_id=decrypted_data["uploader_id"]).first()
                    if user_in_DB is None:
                        safe_uploader_name = re.sub(r"\s", "_", decrypted_data["uploader_name"])
                        user_in_DB = Users.objects.create(
                            server_side_id=decrypted_data["uploader_id"], 
                            name=decrypted_data["uploader_name"],
                            slug=safe_uploader_name + "_" + random_string()
                            )

                    # convert decrypted data into an HttpRequest body for Django Rest Framework to use and save into db
                    save_request = Request(HttpRequest())
                    save_request._full_data = { 
                        "name": image["name"],
                        "url": image["url"],
                        "thumbnail_url": image["thumbnail"],
                        "file_id": image["file_id"],
                        "post_id": decrypted_data["post_id"],
                        "uploader": user_in_DB.id
                    }
                    if "temporary" in decrypted_data: 
                        save_request._full_data["temporary"] = decrypted_data["temporary"]

                    response = super().post(save_request, *args, **kwargs)

                    # if image is only stored temporarily then start a timer to delete newly added record "TTL" seconds from upload
                    if response.data["temporary"]:
                        start_delete_timer(ttl, id=response.data["id"])

                # notify Wayfarer backend about uploaded image location
                update_WF_DB(image_names, decrypted_data["post_id"], decrypted_data["uploader_id"])

                return response
            case _: return HttpResponseBadRequest("Incorrect origin")

    def delete(self, request, *args, **kwargs):
        payload = request.data

        # decrypt incoming data
        if "ac" not in payload or "origin" not in payload: 
            return HttpResponseBadRequest()
        
        encrypted_payload = bytearray(payload["ac"], "utf-8")
        origin = payload["origin"]

        decrypted_data = decrypt(encrypted_payload)

        if "img_names" not in decrypted_data: return HttpResponseBadRequest("Incorrect payload, 'img_names' field is required")

        match origin:
            case "WF":
                for name in decrypted_data["img_names"]:
                    try:
                        image_id = Images.objects.get(name=name).file_id
                        delete_image_external(image_id)
                    except:pass
                    
                    # convert decrypted data into an HttpRequest body for Django Rest Framework to use and delete from db
                    delete_request = Request(HttpRequest())
                    self.imageName = name
                    super().delete(delete_request, *args, **kwargs)
                
                return Response(status=204)

            case _: return HttpResponseBadRequest("Incorrect origin")
  
class ImageUploadView(ListCreateAPIView):
    serializer_class = ImagesSerializer

    context = {}
    context["max_size"] = max_upload_size

    def get(self, request, *args, **kwargs):
        return render(request, "image_upload.html", self.context)

    def post(self, request, *args, **kwargs):
        if request.FILES.getlist("images").__len__() == 0:
            return render(request, "image_upload.html", self.context)
        
        image_files = []
        for image in request.FILES.getlist("images"):
            image_name = re.sub(r"\s", "_", str(image))
            image_binary = image.read()
            mime = magic.from_buffer(image_binary, True)
            if mime.find("image/") == -1:
                context = { **self.context, "error_msg": "Not an image" }
                return render(request, "image_upload.html", context)
            
            if image.size > max_upload_size:
                context = { **self.context, "error_msg": "Image too large" }
                return render(request, "image_upload.html", context)
            
            image_files.append({"src": image_binary, "name": image_name, "mime": mime})
        
        uploader_name = "Medea Guest"
        uploader_slug = re.sub(r"\s", "_", uploader_name)
        guest_user = Users.objects.filter(server_side_id=env("MEDEA_GUEST_ID")).first()
        if guest_user is None:
            guest_user = Users.objects.create(
                server_side_id=env("MEDEA_GUEST_ID"), 
                name=uploader_name,
                slug=uploader_slug
                )
        
        uploaded_images = upload_image_external(image_files, "medea", True)
        image_names = []
        for image in uploaded_images:
            image_names.append({"name": image["name"], "url": image["url"], "thumbnailUrl": image["thumbnail"]})

            # convert decrypted data into an HttpRequest body for Django Rest Framework to use and save into db
            save_request = Request(HttpRequest())
            save_request._full_data = { 
                "name": image["name"],
                "url": image["url"],
                "thumbnail_url": image["thumbnail"],
                "file_id": image["file_id"],
                "uploader": guest_user.id,
                "temporary": True
            }

            response = super().post(save_request, *args, **kwargs)
            start_delete_timer(guest_upload_ttl, id=response.data["id"])
        
        return HttpResponseRedirect("/users/" + uploader_slug)