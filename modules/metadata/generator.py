import os
import re
import json
import random
from typing import Dict, List
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from modules.metadata.retry import safe_chat_completion
from pipeline import JobContext

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_metadata(ctx: JobContext) -> Dict:
    video_metadata = ctx.output["video_metadata"]

    game_title = ctx.input["game_title"]
    tone = ctx.input["tone"]
    original_title = video_metadata["title"]
    original_description = video_metadata["description"]
    transcript = video_metadata["transcript"]
    tags = video_metadata["tags"]
    channel_name = video_metadata["channel"]
    chapters = video_metadata["chapters"]

    summary_payload = {
        "game_title": game_title,
        "tone": tone,
        "transcript": transcript,
        "tags": tags,
        "chapters": chapters,
        "channel_name": channel_name,
    }

    metadata_payload = {
        "game_title": game_title,
        "tone": tone,
        "original_title": original_title,
        "original_description": original_description,
        "tags": tags,
        "channel_name": channel_name,
    }

    summary = summarize(summary_payload)
    metadata = generate_fields(summary, metadata_payload)
    return finalize(metadata, summary)


def summarize(payload) -> str:
    messages: List[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
        ChatCompletionSystemMessageParam(
            role="system",
            content=(
                "You are a gaming content analyst summarizing a full video transcript for metadata generation, title ideation, and viewer engagement. "
                "Use all the provided context to extract meaningful, highlight-worthy moments from the video.\n\n"
                "Prioritize:\n"
                "- Emotional tone shifts (rage, hype, frustration, clutch moments)\n"
                "- Meme-worthy moments (weird deaths, screams, trolling)\n"
                "- Skillful or educational plays (flicks, clutches, rotations, strats)\n"
                "- Specific in-game actions (e.g., recoil reset, map control, grenade lineups)\n"
                "- Map names, gear/loadouts, character roles, or iconic callouts\n\n"
                "**Guidelines:**\n"
                "- Write in plain text only — no Markdown, bullet points, or headings.\n"
                "- Use timestamped highlight notation. Examples:\n"
                "  '[2:13] Clutched a 1v3 on Split with a Sheriff — perfect headshots and comms.'\n"
                "  '[7:05] Screamed after whiffed AWP shot — chat spams LUL.'\n"
                "- Act like you’re prepping clips for a YouTube editor: specific, punchy, and easy to scan.\n"
                "- Stay within 500–800 words. Don’t over-explain. Avoid filler.\n"
            )
        ),
        ChatCompletionUserMessageParam(
            role="user",
            content=(
                    f"Game Title: {payload['game_title']}\n"
                    f"Tone: {payload['tone']}\n"
                    f"Channel Name: {payload['channel_name'] or 'N/A'}\n"
                    f"Tags: {', '.join(payload['tags']) if payload['tags'] else 'None'}\n"
                    f"Chapters:\n"
                    + (
                            "\n".join(
                                f"- {ch.get('title', 'Untitled')} [{ch.get('start_time', 0)}s → {ch.get('end_time', 0)}s]"
                                for ch in (payload['chapters'] or [])
                            ) or "No chapters provided."
                    )
                    + "\n\n"
                      f"Transcript:\n{payload['transcript']}"
            )
        )
    ]

    response = safe_chat_completion(
        client,
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=1200
    )

    return response.choices[0].message.content.strip()


def generate_fields(summary: str, payload) -> Dict:
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
                f"- Match the tone to this style: '{payload['tone']}'. Examples include sarcastic, hype, analytical, chill, funny, toxic and neutral."
            )
        ),
        ChatCompletionUserMessageParam(
            role="user",
            content=(
                "Given the following information, generate YouTube metadata (title + 3-paragraph description).\n\n"
                f"Game Title: {payload['game_title']}\n"
                f"Channel Name: {payload['channel_name'] or 'N/A'}\n"
                f"Original Title: {payload['original_title']}\n"
                f"Original Description: {payload['original_description']}\n"
                f"Relevant Tags: {', '.join(payload['tags']) if payload['tags'] else 'None'}\n"
                f"Tone: {payload['tone']}\n\n"
                f"Summary:\n{summary}\n\n"
                "Respond EXACTLY in this JSON format:\n"
                "{\n"
                "  \"title\": \"<your viral YouTube title without quotes inside>\",\n"
                "  \"description\": \"<3 paragraphs separated by two newlines>\"\n"
                "}"
            )
        )
    ]

    response = safe_chat_completion(
        client,
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


def finalize(metadata: Dict, summary: str) -> Dict:
    return {
        "title": metadata.get("title"),
        "description": metadata.get("description", "").strip(),
        "summary": summary.strip(),
    }
