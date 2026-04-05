import io


from minio import Minio
from fastapi import UploadFile, HTTPException

client = Minio(
    "localhost:9000",
    access_key="myuser",
    secret_key="mysecretpassword",
    secure=False
)
async def put_image_to_minio(avatar: UploadFile, user_id: int):
    file = await avatar.read()
    image_type = avatar.content_type.split("/")[1]
    if image_type not in("jpg", "pdf", "jpeg"):
        raise HTTPException(status_code=400, detail=f"Unsupported image format: {image_type}")
    s3_image = client.put_object("avatars", f"avatar_{user_id}.{image_type}", io.BytesIO(file), length=len(file))
    return s3_image

