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
        final = self.finalize_metadata(metadata)
        return final

    def summarize_transcript_with_gpt35(self, transcript: str) -> str:
        messages: List[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=(
                    "You are a YouTube gaming analyst. Given a full transcript, your job is to create a **detailed, colorful, and story-driven summary** that highlights: "
                    "- Emotional tone shifts"
                    "- Suspicious gameplay (cheating? hacking?)"
                    "- Funny or awkward moments"
                    "- Skillful plays or clutch moments"
                    "- Player interactions and reactions"
                    "Write it with energy and specificity — like you're prepping this for a YouTube content strategist who will write titles and descriptions based on your summary."
                    "Make the summary **at least 400–600 words**. Do not compress — elaborate where it helps."
                    "This will be used as input for GPT-4 to generate titles and descriptions. Make it high quality and expressive."
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
            max_tokens=1000
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
                    "1. 2 viral YouTube title options\n"
                    "2. A compelling video description with energy, humor, and detail\n"
                    "3. A list of **exactly 15 hashtags** that reflect the content, tone, and theme — formatted like `#Tag1 #Tag2 #Tag3`\n\n"
                    f"Summary:\n{summary}\n\n"
                    "Respond in this format:\n"
                    "### Titles:\n"
                    "1. \"Title 1\"\n"
                    "2. \"Title 2\"\n\n"
                    "### Description:\n"
                    "Your description here.\n\n"
                    "### Hashtags:\n"
                    "#one #two #three ... #fifteen\n\n"
                )
            )
        ]

        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            temperature=random.uniform(0.85, 1.0),
            max_tokens=1000
        )

        return self.parse_text_metadata(response.choices[0].message.content.strip())

    def parse_text_metadata(self, raw_text: str) -> dict:
        # titles = re.findall(r'["“](.+?)["”]', raw_text)
        #
        # description_match = re.search(r'Description:\s*(.+?)(?:Hashtags:|$)', raw_text, re.DOTALL | re.IGNORECASE)
        # description = description_match.group(1).strip() if description_match else ""
        #
        # hashtags_match = re.search(r'Hashtags:\s*(.+)', raw_text, re.IGNORECASE)
        # hashtags = re.findall(r'#\w+', hashtags_match.group(1)) if hashtags_match else []
        #
        # return {
        #     "titles": titles[:5],
        #     "description": description,
        #     "hashtags": hashtags,
        #     "raw": raw_text
        # }
        # Extract titles
        titles = re.findall(r'["“](.+?)["”]', raw_text)

        # Extract description
        description_match = re.search(r'Description:\s*(.+?)(?:Hashtags:|Tags:|$)', raw_text, re.DOTALL | re.IGNORECASE)
        description = description_match.group(1).strip() if description_match else ""

        # Extract hashtags (after Hashtags: section)
        hashtags_match = re.search(r'Hashtags:\s*(.+?)(?:Tags:|$)', raw_text, re.DOTALL | re.IGNORECASE)
        hashtags_line = hashtags_match.group(1).strip() if hashtags_match else ""
        hashtags = re.findall(r'#\w+', hashtags_line)

        return {
            "titles": titles[:2],
            "description": description,
            "hashtags": hashtags[:15],
            "raw": raw_text
        }

    def finalize_metadata(self, metadata: dict) -> dict:
        hashtags = metadata.get("hashtags", [])
        clean_hashtags = [f"#{tag.lstrip('#')}" for tag in hashtags]
        description = re.sub(r'\s*#+\s*$', '', metadata['description'].strip(), flags=re.MULTILINE)
        description_with_tags = f"{description}\n\n{' '.join(clean_hashtags)}"

        return {
            **metadata,
            "description": description_with_tags,
        }
