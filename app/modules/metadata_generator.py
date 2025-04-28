import json
import os
import random
import re
from typing import List, Dict
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam


class MetadataGenerator:
    def __init__(self, model_name: str = None):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model_name or "gpt-3.5-turbo"

    def generate(self, transcript_text: str) -> Dict[str, List[str]]:
        summary = self.summarize_transcript_with_gpt35(transcript_text)
        metadata = self.generate_metadata_with_gpt4(summary)
        final = self.finalize_metadata(metadata, summary)
        return final

    def summarize_transcript_with_gpt35(self, transcript: str) -> str:
        messages: List[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=(
                    "You are a YouTube gaming analyst. Given a full transcript, your job is to create a highly detailed, colorful, and story-driven summary that highlights:\n\n"
                    "- Emotional tone shifts (rage, hype, frustration, joy)\n"
                    "- Moments that might raise eyebrows (e.g., unusually fast reactions, weird glitches), but avoid any baseless accusations\n"
                    "- Funny, awkward, meme-worthy moments\n"
                    "- Skillful plays, clutches, slick teamwork, and tactical brilliance\n"
                    "- Noteworthy player interactions, trash talk, teamwork, or friendly banter\n\n"
                    "**Instructions:**\n"
                    "- Write in plain text only — no bullet points, no Markdown formatting, no headings.\n"
                    "- Write with energy, humor, and vivid detail, as if prepping material for a YouTube content strategist creating titles and thumbnails.\n"
                    "- For major moments (big clutches, fails, hilarious events), expand with 2–4 sentences to vividly paint the scene.\n"
                    "- Make the reader feel like they watched it happen live.\n"
                    "- Aim for around 800–1000 words.\n"
                    "- Focus on storytelling and entertainment more than simple summarization."
                )
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=f"Transcript:\n{transcript}"
            )
        ]

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1600
        )

        return response.choices[0].message.content.strip()

    def generate_metadata_with_gpt4(self, summary: str) -> dict:
        messages: List[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=(
                    "You are an expert YouTube metadata strategist for gaming content. "
                    "Your goal is to create highly engaging, SEO-optimized, and emotionally compelling metadata. "
                    "Focus on making the content sound exciting, story-driven, and community-friendly. "
                    "Always write metadata that appeals to YouTube's ranking algorithm while feeling human and entertaining.\n\n"
                    "CRITICAL RULES:\n"
                    "- Respond in strict RFC8259-compliant JSON. Always quote all property names with double quotes. No JavaScript objects. No single quotes. No Markdown. No explanation text. Only valid JSON object.\n"
                    "- Inside all string fields (such as 'description'), escape newlines using `\\n` (backslash-n). Do NOT insert real Enter/Return line breaks inside any string. \n"
                    "- The 'title' must be extremely clickable, emotional, or funny — no quotation marks inside.\n"
                    "- The 'description' must have 3 paragraphs:\n"
                    "  1. Hook the viewer (2–3 strong sentences).\n"
                    "  2. Story or gameplay context (4–5 sentences).\n"
                    "  3. Call to action (invite to subscribe, like, or join a community).\n"
                    "- Separate paragraphs inside the description with `\\n\\n` (two JSON-escaped newlines)."
                    "- The first 2 lines of the description should immediately hook the reader (important for SEO and above-the-fold visibility).\n"
                    "- Use informal, energetic tone fitting for gaming audiences (use emojis, jokes, excitement if appropriate).\n"
                    "- Include 10–15 relevant hashtags inside a JSON list, each starting with '#', no duplicates.\n"
                    "- Do not exceed 2500 characters in the description total."
                )
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=(
                    "Given the following gaming video summary, generate YouTube metadata.\n\n"
                    f"Summary:\n{summary}\n\n"
                    "Respond EXACTLY in this JSON format:\n"
                    "{\n"
                    "  \"title\": \"<your viral YouTube title without quotes inside>\",\n"
                    "  \"description\": \"<3 paragraphs separated by two newlines.>\",\n"
                    "  \"hashtags\": [\"#Tag1\", \"#Tag2\", \"#Tag3\", ..., \"#Tag15\"]\n"
                    "}"
                )
            )
        ]

        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            temperature=random.uniform(0.85, 1.0),
            max_tokens=1500
        )

        raw_content = response.choices[0].message.content.strip()
        parsed = json.loads(raw_content)

        return parsed

    def finalize_metadata(self, metadata: dict, summary: str) -> dict:
        hashtags = metadata.get("hashtags", [])
        clean_hashtags = [f"#{tag.lstrip('#')}" for tag in hashtags]

        description = metadata['description'].strip()
        # No more bold `**` cleaning needed
        description = re.sub(r'\s*#+\s*$', '', description, flags=re.MULTILINE)

        description_with_tags = f"{description}\n\n{' '.join(clean_hashtags)}"

        return {
            **metadata,
            "summary": summary.strip(),
            "description": description_with_tags,
        }
