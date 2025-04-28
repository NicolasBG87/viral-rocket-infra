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
                    "You are a YouTube gaming analyst. Given a full transcript, your job is to create a **detailed, colorful, and story-driven summary** that highlights: "
                    "- Emotional tone shifts (rage, hype, frustration, joy)"
                    "- Moments that *might* raise eyebrows (e.g. unusually fast reactions, weird glitches), but be cautious with accusations — no baseless claims"
                    "- Funny, awkward, or meme-worthy moments"
                    "- Skillful plays, clutch moments, or slick teamwork"
                    "- Noteworthy player interactions, trash talk, teamwork, or friendly banter\n\n"
                    "Write with **energy and specificity**, like you're prepping this for a YouTube content strategist who will craft titles and thumbnails from your summary.\n"
                    "Aim for **1000+ words**, and don't shy away from elaborating when it helps paint the scene.\n"
                    "Focus on storytelling and entertainment."
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
            max_tokens=1200
        )

        return response.choices[0].message.content.strip()

    def generate_metadata_with_gpt4(self, summary: str) -> dict:
        messages: List[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=(
                    "You are an expert YouTube metadata strategist for gaming creators. "
                    "When given a summary of a video, generate metadata that is viral, specific, funny, and emotionally engaging. "
                    "Use bold formatting. Avoid anything generic or boring. Lean into the personality of the content creator."
                )
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=(
                    "Based on this video summary, generate:\n"
                    "1. A viral YouTube title\n"
                    "2. A compelling video description with energy, humor, and detail. Split it into meaningful paragraphs\n"
                    "3. A list of **exactly 15 hashtags** that reflect the content, tone, and theme — formatted like `#Tag1 #Tag2 #Tag3`\n\n"
                    f"Summary:\n{summary}\n\n"
                    "Respond in this format:\n"
                    "### Title:\n"
                    "\"Title\"\n"
                    "### Description:\n"
                    "Paragraph 1.\n\n"
                    "Paragraph 2.\n\n"
                    "Paragraph 3.\n\n"
                    "#Tag1 #Tag2 #Tag3 ... #Tag15\n\n"
                )
            )
        ]

        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            temperature=random.uniform(0.85, 1.0),
            max_tokens=1200
        )

        return self.parse_text_metadata(response.choices[0].message.content.strip())

    def parse_text_metadata(self, raw_text: str) -> dict:
        # Extract title
        title_match = re.search(r'Title:\s*["“](.+?)["”]', raw_text, re.DOTALL | re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else ""

        # Extract description
        description_match = re.search(r'Description:\s*(.+?)(?:#\w+)', raw_text, re.DOTALL | re.IGNORECASE)
        description = description_match.group(1).strip() if description_match else ""

        # Extract hashtags (after description)
        hashtags = re.findall(r'#\w+', raw_text)

        # Clean everything from "**"
        title = title.replace('**', '')
        description = description.replace('**', '')
        hashtags = [tag.replace('**', '') for tag in hashtags]

        return {
            "title": title,
            "description": description,
            "hashtags": hashtags[:15],
            "raw": raw_text
        }

    def finalize_metadata(self, metadata: dict, summary: str) -> dict:
        hashtags = metadata.get("hashtags", [])
        clean_hashtags = [f"#{tag.lstrip('#')}" for tag in hashtags]

        # Clean description and summary
        description = re.sub(r'\s*#+\s*$', '', metadata['description'].strip(), flags=re.MULTILINE)
        description = description.replace('**', '')
        summary = summary.replace('**', '')

        description_with_tags = f"{description}\n\n{' '.join(clean_hashtags)}"

        return {
            **metadata,
            "summary": summary,
            "description": description_with_tags,
        }
