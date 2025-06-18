import os
from google import genai
import re
import json
from typing import Dict
from pipeline import JobContext

client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))


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
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=(
            f"""
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
            
            Topic: {payload['game_title']}
            Additional Context: {payload['game_mode']}
            Tone: {payload['tone']}
            Channel Name: {payload['channel_name'] or 'N/A'}
            Chapters:
            {chr(10).join(f"- {ch.get('title', 'Untitled')} [{ch.get('start_time', 0)}s → {ch.get('end_time', 0)}s]" for ch in (payload['chapters'] or [])) or "No chapters provided."}
            
            Transcript:
            {payload['transcript']}
            """
        )
    )

    return response.text.strip()


def generate_fields(summary: str, payload) -> Dict:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=(
            f"""
           You are an expert YouTube strategist for content creators. 
           Your job is to write **high-converting, SEO-optimized, emotionally compelling metadata** for YouTube videos.
           
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
           
           Given the following information, generate YouTube metadata.
           Topic: {payload['game_title']}
           Channel Name: {payload['channel_name'] or 'N/A'}
           Original Description: {payload['original_description']}
           Tone: {payload['tone']}
           
           Summary:
           {summary}
           """
        )
    )

    raw_content = response.text.strip()

    # Remove Markdown-style code block markers
    raw_content = re.sub(r"^```(?:json)?\s*", "", raw_content)
    raw_content = re.sub(r"\s*```$", "", raw_content)

    # Optional cleanup for escaped characters
    raw_content = raw_content.replace("\\'", "'").replace('\r', '')

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
