import os

import requests

from modules.thumbnail.generator import generate_thumbnail_prompt, generate_thumbnail_image, add_text_top_center
from pipeline import JobContext, step
from util.b2 import upload_to_b2


@step("generate_thumbnail")
def run(ctx: JobContext):
    output_dir = ctx.output_dir
    os.makedirs(output_dir, exist_ok=True)

    raw_path = os.path.join(output_dir, "thumbnail_raw.jpg")
    final_path = os.path.join(output_dir, "thumbnail_final.jpg")

    prompt = generate_thumbnail_prompt(ctx)
    thumbnail_url = generate_thumbnail_image(prompt)

    response = requests.get(thumbnail_url)
    response.raise_for_status()
    with open(raw_path, "wb") as f:
        f.write(response.content)

    overlay_text = ctx.output.get("overlay_text")
    add_text_top_center(raw_path, overlay_text, final_path)

    thumbnail_path = "output/thumbnail_final.jpg"
    b2_key = f"thumbnails/{ctx.job_id}.jpg"

    file_info = upload_to_b2(thumbnail_path, b2_key, "viral-rocket-assets")
    ctx.output["thumbnail_url"] = f"https://f005.backblazeb2.com/file/viral-rocket-assets/{b2_key}"
