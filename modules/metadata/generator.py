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
    mode = ctx.input.get("mode", "standard")

    game_title = ctx.input["game_title"]
    tone = ctx.input["tone"]

    if mode == "standard":
        video_metadata = ctx.output["video_metadata"]

        original_title = video_metadata["title"]
        original_description = video_metadata["description"]
        transcript = video_metadata["transcript"]
        tags = video_metadata["tags"]
        channel_name = video_metadata["channel"]
        chapters = video_metadata["chapters"]
        game_mode = ''
    else:
        original_title = ctx.input.get("original_title", "")
        original_description = ctx.input.get("original_description", "")
        transcript = ctx.input.get("transcript", {})
        tags = ctx.input.get("tags", [])
        channel_name = ctx.input.get("channel", "")
        chapters = ctx.input.get("chapters", [])
        game_mode = ctx.input.get("game_mode", '')

    summary_payload = {
        "game_title": game_title,
        "tone": tone,
        "transcript": transcript,
        "tags": tags,
        "chapters": chapters,
        "channel_name": channel_name,
        "game_mode": game_mode,
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
                "You are a gaming content analyst summarizing a full video for metadata generation, title ideation, and viewer engagement. "
                "Use all the provided context to extract meaningful, highlight-worthy moments from the video.\n\n"
                "Prioritize:\n"
                "- Emotional tone shifts (rage, hype, frustration, clutch moments)\n"
                "- Meme-worthy moments (weird deaths, screams, trolling)\n"
                "- Skillful or educational plays (flicks, clutches, rotations, strats)\n"
                "- Specific in-game actions (e.g., recoil reset, map control, grenade lineups)\n"
                "- Map names, gear/loadouts, character roles, or iconic callouts\n\n"
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
                    f"Game Title: {payload['game_title']}\n"
                    f"Game Mode: {payload['game_mode']}\n"
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
                """
                You are an expert YouTube strategist for gaming creators. 
                Your job is to write **high-converting, SEO-optimized, emotionally compelling metadata** for YouTube gaming videos — including livestreams, patch breakdowns, epic moments, tutorials, or funny compilations.
                
                GOALS:
                - Maximize CTR by writing titles and descriptions that **sound human and exciting**.
                - Use **actual digits** instead of spelled-out numbers (e.g., use "9", not "nine").
                - Use **ALL CAPS** sparingly but strategically for emotional impact or visual emphasis (e.g., INSANE, HUGE BUFFS, LIVE NOW).
                - Include SEO-relevant keywords naturally from the video’s title, tags, or summary.
                - Use a **bold, energetic tone**, like a Twitch or YouTube streamer talking to their fans.
                - Add emojis where relevant to enhance scannability and vibe.
                - Encourage action: phrases like "Watch now", "Don't miss this", "I'm LIVE", etc.
                - Make the description **scannable** with line breaks or bullet-style highlights when listing features or moments.
                
                ADDITIONAL TASK:
                - Generate a short, emotionally compelling **thumbnail overlay text**. 
                - Must feel like something a shocked friend or streamer would say aloud
                - Use emotionally loaded phrasing (e.g., WHAT?!, NO WAY!, WHO DID THIS?!)
                - Keep it between 10 and 20 characters
                - Avoid punctuation except for the "!" and "?"
                - It should make people want to click to find out what happened
                
                RETURN FORMAT:
                Strictly return valid **RFC8259-compliant JSON** with the following fields:
                - "title": string
                - "description": string
                - "overlay_text": string
                
                DO NOT include markdown, comments, or explanations — only valid JSON.
                """
            )
        ),
        ChatCompletionUserMessageParam(
            role="user",
            content=(
                "Given the following information, generate YouTube metadata.\n\n"
                f"Game Title: {payload['game_title']}\n"
                f"Channel Name: {payload['channel_name'] or 'N/A'}\n"
                f"Original Title: {payload['original_title']}\n"
                f"Original Description: {payload['original_description']}\n"
                f"Relevant Tags: {', '.join(payload['tags']) if payload['tags'] else 'None'}\n"
                f"Tone: {payload['tone']}\n\n"
                f"Summary:\n{summary}\n\n"
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
        "overlay_text": metadata.get("overlay_text", "").strip(),
        "summary": summary.strip(),
    }
