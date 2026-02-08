from datetime import datetime
from types import SimpleNamespace
from images.models import Users
import requests
import json
from imagekitio import ImageKit
from imagekitio.file import UploadFileRequestOptions, ListAndSearchFileRequestOptions

from main.settings import env

def __get_imagekit():
    imagekit = ImageKit(
            public_key=env("IMAGEKIT_PUBLIC_KEY"),
            private_key=env("IMAGEKIT_PRIVATE_KEY"),
            url_endpoint=env("IMAGEKIT_URL_ENDPOINT")
        )
    return imagekit

def get_images_external(path: str = "/"):
    admin_user = Users.objects.get(slug=env("ADMIN_SLUG"))

    imagekit = __get_imagekit()
    result = imagekit.list_files(options=ListAndSearchFileRequestOptions(search_query="tags NOT IN ['hidden']", path=path))
    return_value = []
    for img in result.list:
        obj = SimpleNamespace(file_id=img.file_id, name=img.name, url=img.url, created_at=datetime.fromisoformat(img.created_at), uploader=SimpleNamespace(slug=admin_user.slug, name=admin_user.name))
        return_value.append(obj)

    return return_value

def upload_image_external(images: list[dict[str, str | bytes]], folder: str = "/", as_file: bool = False):
    return_value: list[dict[str, str]] = []
    imagekit = __get_imagekit()
    
    for image in images:
        src = (image["name"], image["src"], image["mime"]) if as_file else image["url"]

        upload, = imagekit.upload(
            file=src,
            file_name=image["name"],
            options=UploadFileRequestOptions(
                    response_fields = ["is_private_file", "custom_metadata"],
                    folder = folder,
                    is_private_file = False,
                    overwrite_file = True)
            ),

        print("ImageKit Upload results:", upload.response_metadata.raw)
        transparent_thumbnail = upload.thumbnail_url.replace("tr:n-ik_ml_thumbnail", "tr:n-ik_ml_thumbnail,bg-00000000")
        return_value.append({ "name": upload.name, "file_id": upload.file_id, "url": upload.url, "thumbnail": transparent_thumbnail })

    return return_value

def delete_image_external(image_id: str):
    imagekit =__get_imagekit()
    try:
        delete = imagekit.delete_file(file_id=image_id)
        print("ImageKit Delete results:", delete.response_metadata.raw)
    except Exception as error:
        print(f"Failed to delete file id {image_id} from Imagekit: ", error)

def update_WF_DB(images: list[dict[str, str]], post_id: str, uploader_id: str):
    requests.patch(env("WAYFARER_ENDPOINT") + post_id, data=json.dumps({ 'images': images }), cookies={"userId": str(uploader_id)}, headers={'Content-Type': 'application/json'})
    print("Dispatched request to " + env("WAYFARER_ENDPOINT") + post_id + " with payload: " + json.dumps({ 'images': images }))