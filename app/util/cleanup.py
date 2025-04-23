import os
import shutil
from app.logger import logger

def clean_up(output_dir: str, keep_files=None):
    keep_files = set(keep_files or [])

    if not os.path.exists(output_dir):
        return

    for filename in os.listdir(output_dir):
        file_path = os.path.join(output_dir, filename)
        if filename not in keep_files:
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                logger.debug(f"🧹 Removed: {file_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to remove {file_path}: {e}")

    logger.info(f"🧼 Output directory cleaned: {output_dir}")
