import os
import re

from typing import List
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from PIL import Image, ImageDraw, ImageFont
from modules.metadata.retry import safe_chat_completion
from pipeline import JobContext

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_thumbnail_prompt(ctx: JobContext) -> str:
    game_title = ctx.input.get("game_title")
    title = ctx.output.get("title")
    summary = ctx.output.get("summary")

    messages: List[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
        ChatCompletionSystemMessageParam(
            role="system",
            content=(
                f"Create a clean image for the game: {game_title}. "
                f"Do NOT include any of the following visual elements: YouTube play button, progress bar, timestamps, control icons, video overlays, logos, borders, UI frames, stylized parchment, fantasy overlays, or cinematic frames.\n"
                f"Avoid effects like inset displays, drop shadows, outer image repetition, reflections, screen glare, or frame-in-frame rendering.\n"
                f"Do not generate any part of the YouTube interface or video playback UI — this should be a standalone thumbnail image, **not** a screenshot of a video player.\n"
                f"Render a full edge-to-edge, in-game-like scene that visually resembles high-quality gameplay footage from {game_title}.\n"
                f"The style should match the game's original art direction, colors, character models, camera angles, lighting, and environmental tone.\n"
                f"Avoid artistic reinterpretation — aim for visual fidelity, as if the image was captured from the real game.\n"
                f"Include one key character facing the viewer.\n"
                f"**The character should occupy no more than 35% of the image height.**\n"
                f"Lighting, terrain, armor, and posture should reflect the feel of a moment in high-resolution gameplay.\n\n"
                f"Inspiration from this video summary: {summary}"
            )
        ),
        ChatCompletionUserMessageParam(
            role="user",
            content=(
                f"Game: {game_title}\n"
                f"Title: {title}\n"
                f"Summary: {summary}..."
            )
        )
    ]

    response = safe_chat_completion(
        client,
        model="gpt-4o",
        messages=messages,
        temperature=0.5,
        max_tokens=800
    )

    prompt = response.choices[0].message.content.strip()
    return re.sub(r"^\"|\"$", "", prompt)


def generate_thumbnail_image(prompt: str) -> str:
    response = client.images.generate(
        prompt=prompt,
        model="dall-e-3",
        size="1792x1024",
        n=1,
        response_format="url"
    )
    return response.data[0].url


def resize_image_for_youtube(image_path: str):
    image = Image.open(image_path).convert("RGB")
    image = image.resize((1280, 720), Image.Resampling.LANCZOS)
    image.save(image_path)


def add_text_top_center(image_path: str, text: str, output_path: str):
    # Settings
    image = Image.open(image_path).convert("RGB")
    image = image.resize((1280, 720), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)

    font_path = os.path.join("assets", "burbank.otf")
    primary_size = 175
    secondary_size = int(primary_size * 0.6)
    stroke_width = 8
    margin = 60
    line_spacing = 20
    max_width_ratio = 0.8  # allow a bit more for two-line layouts

    # Load fonts
    try:
        primary_font = ImageFont.truetype(font_path, size=primary_size)
        secondary_font = ImageFont.truetype(font_path, size=secondary_size)
    except IOError:
        primary_font = secondary_font = ImageFont.load_default()

    # Word-wrap into lines
    image_width, _ = image.size
    max_line_width = image_width * max_width_ratio
    words = text.upper().split()
    lines = []
    current = ""
    for w in words:
        test = f"{current} {w}".strip()
        w_box = primary_font.getbbox(test)
        if w_box[2] - w_box[0] <= max_line_width:
            current = test
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)

    # Truncate if too many
    if len(lines) > 4:
        lines = lines[:4]
        lines[-1] += "..."

    # Split into primary + secondary
    if len(lines) > 1:
        primary_line = lines[0]
        secondary_lines = lines[1:]
    else:
        primary_line = lines[0]
        secondary_lines = []

    # Draw primary
    y = margin
    draw.text(
        (margin, y),
        primary_line,
        font=primary_font,
        fill="yellow",
        stroke_width=stroke_width,
        stroke_fill="black"
    )
    # Advance y
    y += primary_font.getbbox(primary_line)[3] - primary_font.getbbox(primary_line)[1] + line_spacing

    # Draw secondary
    for line in secondary_lines:
        draw.text(
            (margin, y),
            line,
            font=secondary_font,
            fill="white",
            stroke_width=int(stroke_width * 0.6),
            stroke_fill="black"
        )
        y += secondary_font.getbbox(line)[3] - secondary_font.getbbox(line)[1] + line_spacing

    image.save(output_path)
