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
        channel_name = video_metadata["channel"]
        chapters = video_metadata["chapters"]
        game_mode = ''
    else:
        original_title = ctx.input.get("original_title", "")
        original_description = ctx.input.get("original_description", "")
        transcript = ctx.input.get("transcript", {})
        channel_name = ctx.input.get("channel", "")
        chapters = ctx.input.get("chapters", [])
        game_mode = ctx.input.get("game_mode", '')

    summary_payload = {
        "game_title": game_title,
        "tone": tone,
        "transcript": transcript,
        "chapters": chapters,
        "channel_name": channel_name,
        "game_mode": game_mode,
    }

    metadata_payload = {
        "game_title": game_title,
        "tone": tone,
        "original_title": original_title,
        "original_description": original_description,
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
                """
                You are a gaming content analyst summarizing a full video for metadata generation, title ideation, and viewer engagement.
                Use all the provided context to extract meaningful, highlight-worthy moments from the video.
                
                GOALS (Prioritize):
                - Emotional tone shifts (rage, hype, frustration, clutch moments)
                - Meme-worthy moments (weird deaths, screams, trolling)
                - Skillful or educational plays (flicks, clutches, rotations, strats)
                - Specific in-game actions (e.g., recoil reset, map control, grenade lineups)
                - Map names, gear/loadouts, character roles, or iconic callouts
                
                CRITICAL RULES:
                - Write in plain text only — no bullet points, no Markdown formatting, no headings
                - Write like you’re preparing a highlight timeline for a YouTube editor
                - Keep it engaging, but lean into practical/educational context when relevant
                - Final output should read like an annotated highlight log crossed with an entertaining play-by-play
                - Aim for 500–800 words max — don't fill it with fluff
                """
            )
        ),
        ChatCompletionUserMessageParam(
            role="user",
            content=(
                    f"Game Title: {payload['game_title']}\n"
                    f"Game Mode: {payload['game_mode']}\n"
                    f"Tone: {payload['tone']}\n"
                    f"Channel Name: {payload['channel_name'] or 'N/A'}\n"
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
                Your job is to write **high-converting, SEO-optimized, emotionally compelling metadata** for YouTube gaming videos.
                
                GOALS:
                - Maximize CTR by writing titles, descriptions and overlay texts that **sound human and exciting**
                - Use **actual digits** instead of spelled-out numbers (e.g., use "9", not "nine")
                - Use **ALL CAPS** sparingly but strategically for emotional impact or visual emphasis (e.g., INSANE, HUGE BUFFS, LIVE NOW)
                - Include SEO-relevant keywords naturally from the video’s title, description, or summary
                
                TITLE RULES:
                - Include power words like "INSANE," "EPIC," "SECRET," "UNBELIEVABLE," etc.  
                - Avoid generic phrases like "Part 1" or "Gameplay."  
                - Prioritize curiosity and excitement. 
                - Keep it under 60 characters
                
                TITLE FORMAT EXAMPLES:
                - "INSANE 1v5 CLUTCH in [Game Name]! (Unbelievable Ending!)"  
                - "How to DOMINATE as [Character/Class] in [Game Name]"  
                - "I Found the RAREST Item in [Game Name]… And It BROKE the Game!"  
                - "[Game Name] But EVERY KILL Upgrades My Weapon!"  
                - "This SECRET Boss Took Me 100 Tries… Was It Worth It?" 
                
                DESCRIPTION RULES:
                - Make the description **scannable** with line breaks or bullet-style highlights when listing features or moments
                - Add emojis where relevant to enhance vibe, emotion, and visual flow
                - Include clear calls-to-action when appropriate
                - Include timestamps and social media links if they exist in the original description
                - Avoid long paragraphs
                
                OVERLAY TEXT RULES:
                - Generate emotionally charged thumbnail overlay text split into **two parts**:
                  - "overlay_text_primary": the leading hook (up to 2 impactful words)
                  - "overlay_text_secondary": the punch or outcome (up to 3 words)
                - Combined length should be ≤30 characters
                - Make viewers **desperate to know what happened**
                - Use only **letters, numbers, and spaces** (no emojis, punctuation, symbols or any other special characters.)
                
                RETURN FORMAT:
                Strictly return valid **RFC8259-compliant JSON** with the following fields:
                - "title": string
                - "description": string
                - "overlay_text_primary": string
                - "overlay_text_secondary": string
                
                DO NOT include markdown, comments, or explanations — only valid JSON.
                CRITICAL: All double quotes inside values must be escaped like \", and strings must use double quotes around keys and values.
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
        "overlay_text_primary": metadata.get("overlay_text_primary", "").strip(),
        "overlay_text_secondary": metadata.get("overlay_text_secondary", "").strip(),
        "summary": summary.strip(),
    }
