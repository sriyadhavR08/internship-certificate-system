import base64
import os
import uuid
from pathlib import Path


def save_base64_file(data_uri, media_folder, subfolder="uploads", prefix="file"):
    """
    Decodes a base64 Data URL and saves it to the media folder.
    Returns the relative path from media folder (e.g. 'selfies/selfie_abc123.jpg').
    """
    if not data_uri:
        return None
    if not isinstance(data_uri, str) or not data_uri.startswith("data:"):
        # If it's already a saved filename/url, return as is
        return data_uri

    try:
        header, encoded = data_uri.split(";base64,", 1)
        mime = header.split(":", 1)[-1].split(";")[0].lower()
        ext = mime.split("/")[-1] if "/" in mime else "jpg"
        if ext in ["jpeg", "jpg"]:
            ext = "jpg"
        elif ext == "png":
            ext = "png"
        elif ext == "webp":
            ext = "webp"
        elif ext == "pdf":
            ext = "pdf"
        else:
            ext = "jpg"

        decoded = base64.b64decode(encoded)
        filename = f"{prefix}_{uuid.uuid4().hex[:10]}.{ext}"

        target_dir = Path(media_folder) / subfolder
        target_dir.mkdir(parents=True, exist_ok=True)

        file_path = target_dir / filename
        with open(file_path, "wb") as f:
            f.write(decoded)

        # Return relative path for database storage (matching Django format)
        return f"{subfolder}/{filename}"
    except Exception as e:
        print(f"Error saving base64 file: {e}")
        return None
