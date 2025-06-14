import os
import re

from typing import List
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from modules.metadata.retry import safe_chat_completion
from pipeline import JobContext

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_thumbnail_prompt(ctx: JobContext) -> str:
    game_title = ctx.input.get("game_title")
    game_summary = ctx.output.get("summary")

    messages: List[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
        ChatCompletionSystemMessageParam(
            role="system",
            content=(
                """
                You are an expert prompt engineer image generation.  
                Your job is to craft a high-quality image prompt for an AI image generation model to create an image for a gaming video.
                
                GOALS:
                - Create a clean image for the provided game title.
                - Do NOT include any of the following visual elements: YouTube play button, progress bar, timestamps, control icons, video overlays, logos, borders, UI frames, stylized parchment, fantasy overlays, or cinematic frames.
                - Avoid effects like inset displays, drop shadows, outer image repetition, reflections, screen glare, or frame-in-frame rendering.
                - Do not generate any part of the YouTube interface or video playback UI — this should be a standalone thumbnail image, **not** a screenshot of a video player.
                - Render a full edge-to-edge, in-game-like scene that visually resembles high-quality gameplay footage from [game_title].
                - The style should match the game's original art direction, colors, character models, camera angles, lighting, and environmental tone.
                - Avoid artistic reinterpretation — aim for visual fidelity, as if the image was captured from the real game.
                - Lighting, terrain, armor, and posture should reflect the feel of a moment in high-resolution gameplay.
                - Optionally include one key character or object.
                - Keep the character in the right side of the image.
                - Inspiration from this video summary: [game_summary]
                
                RETURN FORMAT:
                Strictly return the image prompt text. No preamble, no explanation.
                """
            )
        ),
        ChatCompletionUserMessageParam(
            role="user",
            content=(
                "Given the following information, generate image generation prompt.\n\n"
                f"game_title: {game_title}\n"
                f"game_summary:\n{game_summary}\n\n"
            )
        )
    ]

    response = safe_chat_completion(
        client,
        model="gpt-4o",
        messages=messages,
        temperature=0.3,
        max_tokens=1200
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


from PIL import Image, ImageDraw, ImageFont
import os


def add_text_to_image(image_path: str, output_path: str, primary_text: str, secondary_text: str):
    # Settings
    image = Image.open(image_path).convert("RGB")
    image = image.resize((1280, 720), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)

    font_path = os.path.join("assets", "burbank.otf")
    primary_size = 150
    secondary_size = int(primary_size * 0.6)
    stroke_width = 8
    margin = 20
    line_spacing = 20

    # Load fonts
    try:
        primary_font = ImageFont.truetype(font_path, size=primary_size)
        secondary_font = ImageFont.truetype(font_path, size=secondary_size)
    except IOError:
        primary_font = secondary_font = ImageFont.load_default()

    # Start drawing from top-left
    x = margin
    y = margin

    # Draw primary text
    draw.text(
        (x, y),
        primary_text.upper(),
        font=primary_font,
        fill="yellow",
        stroke_width=stroke_width,
        stroke_fill="black"
    )
    y += primary_font.getbbox(primary_text)[3] - primary_font.getbbox(primary_text)[1] + line_spacing

    # Draw secondary text
    if secondary_text:
        draw.text(
            (x, y),
            secondary_text.upper(),
            font=secondary_font,
            fill="white",
            stroke_width=int(stroke_width * 0.6),
            stroke_fill="black"
        )

    # Save image
    image.save(output_path)
