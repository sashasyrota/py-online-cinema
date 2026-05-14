import io
import os

import boto3
from minio import Minio
from fastapi import UploadFile, HTTPException

client = Minio(
    f"{os.getenv("MINIO_HOST")}:{os.getenv("MINIO_PORT")}",
    access_key="myuser",
    secret_key="mysecretpassword",
    secure=False,
)

async def put_image_to_minio(avatar: UploadFile, user_id: int):
    avatar_file = await avatar.read()
    image_type = avatar.content_type.split("/")[1]
    if image_type not in ("jpg", "pdf", "jpeg"):
        raise HTTPException(
            status_code=400, detail=f"Unsupported image format: {image_type}"
        )
    s3_image = client.put_object(
        "avatars",
        f"avatar_{user_id}.{image_type}",
        io.BytesIO(avatar_file),
        length=len(avatar_file),
    )
    return s3_image
