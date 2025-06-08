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
                f"Create a YouTube thumbnail based on the game {game_title}. "
                f"Do NOT include any of the following visual elements: YouTube play button, logos, borders, UI frames, stylized parchment, fantasy overlays, or cinematic frames.\n"
                f"Also avoid effects like inset displays, drop shadows, outer image repetition, reflection, or frame-in-frame rendering.\n"
                f"Render a full edge-to-edge, fake in-game scene that visually resembles actual gameplay from {game_title}.\n"
                f"The style should match the game's original art direction, colors, character models, camera angles, lighting, and environmental tone.\n"
                f"Avoid artistic reinterpretation — aim for visual fidelity, as if the image was captured from the real game.\n"
                f"Include one key character facing the viewer. Do not place it in the center, top or left.\n"
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


def add_text_top_center(image_path: str, text: str, output_path: str):
    image = Image.open(image_path).convert("RGB")
    image = image.resize((1280, 720), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)

    # Load Impact from assets folder
    font_path = os.path.join("assets", "impacted.ttf")
    font_size = 175
    side_margin = 60
    line_spacing = 20

    max_width_ratio = 0.4

    try:
        font = ImageFont.truetype(font_path, size=font_size)
    except IOError:
        font = ImageFont.load_default()

    image_width, image_height = image.size
    max_line_width = image_width * max_width_ratio
    text = text.upper()

    # Manual word wrapping
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        line_width = font.getbbox(test_line)[2] - font.getbbox(test_line)[0]
        if line_width <= max_line_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    if len(lines) > 3:
        lines = lines[:3]
        lines[-1] += "..."

    # Calculate Y position
    total_height = sum(font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines) + (
            len(lines) - 1) * line_spacing
    current_y = (image_height - total_height) // 2

    for line in lines:
        draw.text(
            (side_margin, current_y),
            line,
            font=font,
            fill="white",
            stroke_width=10,
            stroke_fill="black"
        )
        current_y += font.getbbox(line)[3] - font.getbbox(line)[1] + line_spacing

    image.save(output_path)
