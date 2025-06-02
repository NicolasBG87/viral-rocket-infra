import json
import os
import random
import re
from typing import List, Dict
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from app.util.retry_gpt import safe_chat_completion


class MetadataGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate(self, game_title: str, transcript_text: str) -> Dict[str, List[str]]:
        try:
            summary = self.summarize_transcript(game_title, transcript_text)
            metadata = self.generate_metadata(summary)
            final = self.finalize_metadata(metadata, summary)
            return final
        except Exception as e:
            raise RuntimeError(f"Error: {e}")

    def generate_user_enhanced(self, game_title: str, transcript: str, payload: Dict) -> Dict[str, List[str]]:
        try:
            summary = self.summarize_user_enhanced_details(game_title, transcript, payload)
            metadata = self.generate_metadata(summary)
            final = self.finalize_metadata(metadata, summary)
            return final
        except Exception as e:
            raise RuntimeError(f"Error: {e}")

    def summarize_user_enhanced_details(self, game_title, transcript, payload):
        video_type = payload.get('video_type')
        game_mode = payload.get('game_mode')

        messages: List[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=(
                    "You are a gaming content analyst summarizing a full video transcript, game title, video type and game mode for metadata generation, title ideation, and viewer engagement. Focus on:\n\n"
                    "Note: The transcript is likely made up of in-game system sounds and callouts.\n"
                    "- Emotional tone shifts (rage, hype, frustration, clutch moments)\n"
                    "- Funny or meme-worthy moments (weird deaths, misplays, screams)\n"
                    "- Skillful or educational moments (clutches, flicks, smokes, lineups, strategy calls)\n"
                    "- Specific in-game actions (e.g. crosshair control, recoil reset, map control, team pushes)\n"
                    "- Noteworthy callouts, gear mentions, map names, or settings\n\n"
                    "**Instructions:**\n"
                    "- Write in plain text only — no bullet points, no Markdown formatting, no headings.\n"
                    "- Prioritize detail, but label moments clearly. For example:\n"
                    "  '[2:13] Player lands 1v3 clutch on Mirage using AK — smooth spray control and perfect crosshair placement.'\n"
                    "  '[4:42] Rage moment after whiffed AWP shot — teammate laughs in VC.'\n"
                    "- Write like you’re preparing a highlight timeline for a YouTube editor.\n"
                    "- Keep it engaging, but lean into practical/educational context when relevant.\n"
                    "- Final output should read like an annotated highlight log crossed with an entertaining play-by-play.\n"
                    "- Aim for 500–800 words max — don't fill it with fluff."
                )

            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=(
                    f"Game Title: {game_title}\n"
                    f"Video Type: {video_type}\n"
                    f"Transcript:\n{transcript}\n"
                    f"Game Mode:\n{game_mode}\n"
                )
            )
        ]

        response = safe_chat_completion(
            self.client,
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=1200
        )

        return response.choices[0].message.content.strip()

    def summarize_transcript(self, game_title: str, transcript: str) -> str:
        messages: List[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=(
                    "You are a gaming content analyst summarizing a full video transcript for metadata generation, title ideation, and viewer engagement. Focus on:\n\n"
                    "- Emotional tone shifts (rage, hype, frustration, clutch moments)\n"
                    "- Funny or meme-worthy moments (weird deaths, misplays, screams)\n"
                    "- Skillful or educational moments (clutches, flicks, smokes, lineups, strategy calls)\n"
                    "- Specific in-game actions (e.g. crosshair control, recoil reset, map control, team pushes)\n"
                    "- Noteworthy callouts, gear mentions, map names, or settings\n\n"
                    "**Instructions:**\n"
                    "- Write in plain text only — no bullet points, no Markdown formatting, no headings.\n"
                    "- Prioritize detail, but label moments clearly. For example:\n"
                    "  '[2:13] Player lands 1v3 clutch on Mirage using AK — smooth spray control and perfect crosshair placement.'\n"
                    "  '[4:42] Rage moment after whiffed AWP shot — teammate laughs in VC.'\n"
                    "- Write like you’re preparing a highlight timeline for a YouTube editor.\n"
                    "- Keep it engaging, but lean into practical/educational context when relevant.\n"
                    "- Final output should read like an annotated highlight log crossed with an entertaining play-by-play.\n"
                    "- Aim for 500–800 words max — don't fill it with fluff."
                    "- At the very end of your output, include this line:\n"
                    "[TONE]: <dominant tone label>, such as sarcastic, hype, analytical, chill, funny, toxic or neutral."

                )
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=(
                    f"Game Title: {game_title}\n"
                    f"Transcript:\n{transcript}\n"
                )
            )
        ]

        response = safe_chat_completion(
            self.client,
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=1200
        )

        return response.choices[0].message.content.strip()

    def generate_metadata(self, summary: str) -> dict:
        # Extract tone from end of summary
        tone_match = re.search(r"\[TONE\]:\s*(\w+)", summary, re.IGNORECASE)
        tone = tone_match.group(1).lower() if tone_match else "neutral"

        # Remove the tone line from the summary before prompting
        summary = re.sub(r"\[TONE\]:.*", "", summary).strip()

        messages: List[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=(
                    "You are an expert YouTube metadata strategist specialized in gaming content like FPS tutorials, stream highlights, and educational gameplay. "
                    "Your job is to generate high-converting, SEO-optimized metadata that ranks well, sounds human, and clearly communicates value to gamers.\n\n"
                    "CRITICAL RULES:\n"
                    "- Respond in strict RFC8259-compliant JSON. Always quote all property names with double quotes. No JavaScript objects. No single quotes around keys. No Markdown. No explanation text. Only valid JSON object.\n"
                    "- Do NOT include unescaped double quotes inside any string. Prefer single quotes or escape them using `\\\"`.\n"
                    "- Do NOT escape single quotes (e.g., don’t use \\\'). Use plain `'` instead.\n"
                    "- Inside all string fields (such as 'description'), escape newlines using `\\n`. Do NOT insert actual line breaks.\n\n"
                    "TITLE:\n"
                    "- Must include 1–2 core YouTube search keywords relevant to the game and video type.\n"
                    "- Must sound exciting, urgent, or transformative — no clickbait vagueness.\n"
                    "- Be clear and searchable — avoid vague phrases like 'game-changing', 'crazy update', or 'next-level strategy'.\n"
                    "- Avoid quotation marks.\n\n"
                    "DESCRIPTION:\n"
                    "- Must include exactly 3 paragraphs:\n"
                    "  1. Hook the viewer with 1–2 short, exciting lines. Use strong phrasing, stats, or surprising outcomes.\n"
                    "  2. Briefly summarize the key gameplay changes or insights (no fluff). Mention specifics: classes, abilities, gear, etc.\n"
                    "  3. Finish with a direct, tone-matching CTA. Avoid “smash subscribe” — instead, ask a question that sparks comments or invites feedback.\n"
                    "- Keep the tone aligned with the detected tone style (e.g. sarcastic, hype, or analytical).\n"
                    "- Description must stay under 800 characters if possible — prioritize clarity and scannability.\n"
                    "- Use `\\n\\n` to separate paragraphs.\n\n"
                    "EXTRA INSTRUCTIONS:\n"
                    "- Tailor your output to gaming viewers looking for *specific solutions* (e.g. how to aim better, reduce recoil, or stop whiffing shots).\n"
                    "- Avoid abstract phrases like 'zen', 'epic', or 'unleash your true potential'. Be tactical, not poetic.\n"
                    "- Do NOT write vague generalizations like 'improve your skills' — say exactly *what* they'll improve and *how*.\n"
                    "- Prefer numbers, stat changes, gear names, and player-relevant terms over vague phrases.\n"
                    "- Avoid repeating ideas across paragraphs.\n"
                    "- Focus on what changes, why it matters, and what the viewer should do next.\n"
                    f"- Match the tone to this style: '{tone}'. Examples include sarcastic, hype, analytical, chill, funny, toxic and neutral."
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
                    "  \"description\": \"<3 paragraphs separated by two newlines.>\"\n"
                    "}"
                )
            )
        ]

        response = safe_chat_completion(
            self.client,
            model="gpt-4o",
            messages=messages,
            temperature=random.uniform(0.6, 0.85),
            max_tokens=1000
        )

        raw_content = response.choices[0].message.content.strip()
        raw_content = re.sub(r"^```(?:json)?\s*", "", raw_content)
        raw_content = re.sub(r"\s*```$", "", raw_content)
        raw_content = raw_content.replace("\\'", "'").replace('\r', '')
        raw_content = re.sub(r'\\([^"\\/bfnrtu])', r'\\\\\1', raw_content)

        if not raw_content.startswith("{"):
            raise RuntimeError(f"Expected JSON, got:\n{raw_content[:300]}")

        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse JSON:\n{raw_content}\n\nError: {e}")

        return parsed

    def finalize_metadata(self, metadata: dict, summary: str) -> dict:
        description = metadata['description'].strip()
        description = re.sub(r'\s*#+\s*$', '', description, flags=re.MULTILINE)

        return {
            "title": metadata["title"],
            "description": description,
            "summary": summary.strip()
        }
