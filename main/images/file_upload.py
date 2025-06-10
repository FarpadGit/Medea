import requests
import json
from imagekitio import ImageKit
from imagekitio.file import UploadFileRequestOptions

from main.settings import env

def upload_image_external(images: list[dict[str, str]]):
    return_value: list[dict[str, str]] = []
    imagekit = ImageKit(
            public_key=env("IMAGEKIT_PUBLIC_KEY"),
            private_key=env("IMAGEKIT_PRIVATE_KEY"),
            url_endpoint=env("IMAGEKIT_URL_ENDPOINT")
        )
    
    for image in images:
        upload, = imagekit.upload(
            file=image["src"],
            file_name=image["name"],
            options=UploadFileRequestOptions(
                    response_fields = ["is_private_file", "custom_metadata"],
                    is_private_file = False,
                    overwrite_file = True)
            ),

        print("ImageKit Upload results:", upload.response_metadata.raw)
        transparent_thumbnail = upload.thumbnail_url.replace("tr:n-ik_ml_thumbnail", "tr:n-ik_ml_thumbnail,bg-00000000")
        return_value.append({ "name": upload.name, "file_id": upload.file_id, "url": upload.url, "thumbnail": transparent_thumbnail })

    return return_value

def delete_image_external(image_id: str):
    imagekit = ImageKit(
            public_key=env("IMAGEKIT_PUBLIC_KEY"),
            private_key=env("IMAGEKIT_PRIVATE_KEY"),
            url_endpoint=env("IMAGEKIT_URL_ENDPOINT")
        )
    
    delete = imagekit.delete_file(file_id=image_id)
    print("ImageKit Delete results:", delete.response_metadata.raw)

def update_WF_DB(images: list[dict[str, str]], post_id: str, uploader_id: str):
    print("sending Patch to:", env("WAYFARER_ENDPOINT") + post_id)
    print("with data:", json.dumps({ 'images': images }), "userId:", uploader_id)
    requests.patch(env("WAYFARER_ENDPOINT") + post_id, data=json.dumps({ 'images': images }), cookies={"userId": uploader_id}, headers={'Content-Type': 'application/json'})