import re
from django.views.generic import ListView
from django.http import HttpResponseBadRequest
from rest_framework.generics import ListCreateAPIView, DestroyAPIView
from rest_framework.request import Request, HttpRequest
from rest_framework.response import Response

from main.settings import env
from .models import Users, Images, ttl
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
            return HttpResponseBadRequest()
        
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
                        uploader_name = re.sub(r"\s", "_", decrypted_data["uploader_name"])
                        user_in_DB = Users.objects.create(
                            server_side_id=decrypted_data["uploader_id"], 
                            name=uploader_name,
                            slug=uploader_name + "_" + random_string()
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