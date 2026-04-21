import uuid
from io import BytesIO
from PIL import Image, ImageOps
import boto3
from starlette.concurrency import run_in_threadpool
from config import settings

# from pathlib import Path
# PROFILE_PICS_DIR = Path('media/profile_pics')

def _get_s3_client():
    return boto3.client(
        "s3",
        region_name=settings.s3_region,
        aws_access_key_id=(
            settings.s3_access_key_id.get_secret_value() if settings.s3_access_key_id else None
        ),
        aws_secret_access_key=(
            settings.s3_secret_access_key.get_secret_value() if settings.s3_secret_access_key else None
        ),
        endpoint_url=settings.s3_endpoint_url
    )

## Process Image Function
def process_profile_image(content: bytes) -> tuple[bytes, str]:
    with Image.open(BytesIO(content)) as original:  ## Transforming uploaded file (bytes) into a Image Object
        img = ImageOps.exif_transpose(original)     ## Fixing image orientation

        img = ImageOps.fit(img, (300, 300), method=Image.Resampling.LANCZOS)        #Fixing image dimensions

        if img.mode in ("RGBA", "LA", "P"):             ## Fixing image colors
            img = img.convert("RGB")

        filename = f"{uuid.uuid4().hex}.jpg"
        # filepath = PROFILE_PICS_DIR / filename          ## Setting a filepath name
        # PROFILE_PICS_DIR.mkdir(parents=True, exist_ok=True)         ## Creating the filepath

        output = BytesIO()
        img.save(output, "JPEG", quality=85, optimize=True)    
        output.seek(0)      ## Saving image

    return output.read(), filename             ## Returns image path

def _upload_to_s3(file_bytes: bytes, key: str) -> None:
    s3 = _get_s3_client()
    s3.upload_fileobj(
        BytesIO(file_bytes),
        settings.s3_bucket_name,
        key,
        ExtraArgs={"ContentType": "image/jpeg"}
    )

def _delete_from_s3(key: str) -> None:
    s3 = _get_s3_client()
    s3.delete_object(Bucket=settings.s3_bucket_name, Key=key)

async def upload_profile_image(file_bytes: bytes, filename:str) -> None:
    key = f"profile_pics/{filename}"        # The key must match the bucket policy.
    await run_in_threadpool(_upload_to_s3, file_bytes, key)

async def delete_profile_image(filename: str | None) -> None:
    if filename is None:
        return
    key = f"profile_pics/{filename}"        # The key must match the bucket policy.
    await run_in_threadpool(_delete_from_s3, key)