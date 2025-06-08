from b2sdk.v2 import InMemoryAccountInfo, B2Api
from pathlib import Path
import os

def upload_to_b2(local_path: str, b2_filename: str, bucket_name: str):
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)

    # These should come from your environment or secrets
    app_key_id = os.getenv("B2_KEY_ID")
    app_key = os.getenv("B2_APP_KEY")

    b2_api.authorize_account("production", app_key_id, app_key)

    bucket = b2_api.get_bucket_by_name(bucket_name)
    file_path = Path(local_path)

    with file_path.open("rb") as file:
        file_info = bucket.upload_bytes(
            file.read(),
            file_name=b2_filename,
            content_type="image/png"
        )
        return file_info
