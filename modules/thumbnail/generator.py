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
            Your task is to craft a highly detailed image prompt for a gaming YouTube video. The AI will use this prompt to generate a single high-quality image.
             
            GOALS:
            - Create a clean, minimalistic, edge-to-edge image in the style of the game
            - Match the original art style, colors, character models, lighting, and environment
            - Include one key character or object to serve as the visual focal point
            - Make it immersive, cinematic, and ideal for a YouTube gaming image
             
            IMPORTANT CONTEXT:
            - The image must depict a fictional moment from a **video game**, not the real world.
            - All elements must look like they were captured **in-game** using the game's original art style and lighting.
             
            CRITICAL RULES:
            - Do NOT include: YouTube play buttons, timestamps, overlays, borders, logos, UI frames, stylized parchment, fantasy scrolls, cinematic frames, or any video player elements
            - Do NOT crop or scale the scene — the image must be full-bleed, edge-to-edge
            - Do NOT add text, lettering, signs, symbols, or written words anywhere in the image
            - Avoid visual effects like drop shadows, inset displays, outer reflections, screen glare, or frame-in-frame rendering
            - Avoid stylization or reinterpretation — aim for visual accuracy and realism as if captured in-game
             
            RETURN FORMAT:
            - Strictly return only the final image generation prompt. Do not include any explanation or preamble.
            
            Given the following information, generate image generation prompt.
            Game: {game_title}
            Video title:{title}
            Summary:
            {summary}
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
