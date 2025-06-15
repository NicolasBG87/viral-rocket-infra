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
                 You are an expert prompt engineer for AI image generation.
                 Your task is to craft a highly detailed image prompt for a gaming YouTube thumbnail. The AI will use this prompt to generate a single high-quality image.
                 Start by reading the game summary provided.
                 From the summary, pick **one** moment that would make the most eye-catching, emotionally charged scene for a thumbnail.
                 This could be a rage moment, a clutch play, a funny death, or anything visually dramatic.
                 Then, based on that scene, write a high-resolution image prompt following these rules:
                 
                 GOALS:
                 - Create a clean, edge-to-edge image in the style of the game
                 - Match the original art style, colors, character models, lighting, and environment
                 - Include one key character or object to serve as the visual focal point
                 - Place the subject on the **right-hand side** or **bottom-right corner**, leaving space on top-left for text
                 - Make it immersive, cinematic, and ideal for a YouTube gaming thumbnail
                 
                 IMPORTANT CONTEXT:
                 - The thumbnail must depict a fictional moment from a **video game**, not the real world.
                 - All elements must look like they were captured **in-game** using the game's original art style and lighting.
                 
                 CRITICAL RULES:
                 - Do NOT include: YouTube play buttons, timestamps, overlays, borders, logos, UI frames, stylized parchment, fantasy scrolls, cinematic frames, or any video player elements
                 - Do NOT crop or scale the scene — the image must be full-bleed, edge-to-edge
                 - Avoid visual effects like drop shadows, inset displays, outer reflections, screen glare, or frame-in-frame rendering
                 - Avoid stylization or reinterpretation — aim for visual accuracy and realism as if captured in-game
                 - **Absolutely no text, lettering, signs, symbols, or written words anywhere in the image**
                 
                 RETURN FORMAT:
                 - Strictly return only the final image generation prompt. Do not include any explanation or preamble.
                 - Stay under 3 sentences and 350 characters.
                 """
            )
        ),
        ChatCompletionUserMessageParam(
            role="user",
            content=(
                "Given the following information, generate image generation prompt.\n\n"
                f"Game title: {game_title}\n"
                f"Game summary:\n{game_summary}\n\n"
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
    try:
        response = client.images.generate(
            prompt=prompt,
            model="dall-e-3",
            size="1792x1024",
            n=1
        )
        return response.data[0].url
    except Exception as e:
        raise RuntimeError(f"Image generation failed: {e}, prompt was: {prompt}")


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
    primary_size = 175
    secondary_size = int(primary_size * 0.6)
    stroke_width = 8
    margin = 60
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
