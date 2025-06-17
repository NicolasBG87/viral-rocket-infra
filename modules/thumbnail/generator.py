import os
from io import BytesIO
from google.genai import types
from google import genai
from pipeline import JobContext
from PIL import Image, ImageDraw, ImageFont

client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))


def generate_thumbnail_prompt(ctx: JobContext) -> str:
    game_title = ctx.input.get("game_title")
    summary = ctx.output.get("summary")
    title = ctx.output.get("title")

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=(
            f"""
            You are an expert prompt engineer for AI image generation.
            Your task is to craft a highly detailed, cinematic, and immersive image prompt for a gaming YouTube video thumbnail. The AI will use this prompt to generate a single high-quality, full-bleed, edge-to-edge image in a 16:9 aspect ratio.

            GOALS:
            - Generate a clean, minimalistic image directly from the game's original art style.
            - Replicate the exact art style, color palette, character models, environmental details, and lighting of the specified game.
            - The image must feature one central key character or significant object from the game as the primary visual focal point positioned in the bottom-right corner.
            - The scene should feel like a dynamic, in-game moment, ideal for a YouTube gaming thumbnail.

            IMPORTANT CONTEXT:
            - The image must depict a fictional moment *within* the **video game environment**, not the real world.
            - All visual elements must appear as if captured directly **in-game**, utilizing the game's native graphics and lighting engine.

            CRITICAL RULES:
            - **Do NOT** include any YouTube branding: no play buttons, timestamps, overlays, borders, logos, UI frames, stylized parchment, fantasy scrolls, cinematic frames, or any video player specific elements.
            - **Do NOT** crop or scale the scene; the image must be full-bleed and edge-to-edge.
            - **Do NOT** add any form of text, lettering, signs, symbols, or written words anywhere within the image.
            - **Avoid** visual effects like drop shadows, inset displays, outer reflections, screen glare, or frame-in-frame rendering.
            - **Avoid** any stylization or reinterpretation of the game's visuals. Aim for complete visual accuracy and photorealism as if it were a direct in-game screenshot.

            Given the following information, generate the image generation prompt. Focus on describing the specific scene, character/object, environment, and mood based on the summary and title.

            Game: {game_title}
            Video title: {title}
            Summary: {summary}
            """
        )
    )

    return response.text.strip()


def generate_thumbnail_image(prompt: str, path: str):
    try:
        response = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9"
            )
        )

        for generated_image in response.generated_images:
            image = Image.open(BytesIO(generated_image.image.image_bytes))
            image.save(path)

    except Exception as e:
        raise RuntimeError(f"Image generation failed: {e}, prompt was: {prompt}")


def resize_image_for_youtube(image_path: str):
    image = Image.open(image_path).convert("RGB")
    image = image.resize((1280, 720), Image.Resampling.LANCZOS)
    image.save(image_path)


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
