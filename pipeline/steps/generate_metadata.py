from pipeline import JobContext, step
from modules.metadata.generator import generate_metadata
from util import logger


@step("generate_metadata")
def run(ctx: JobContext):
    mode = ctx.input.get("mode", "standard")
    output = ctx.output

    if mode == "standard":
        score = output.get("video_metadata").get("transcript_score", 0)
        transcript = output.get("video_metadata").get("transcript")
        if not transcript:
            raise RuntimeError("No transcript available for metadata generation")

        if score >= 0.5:
            logger.info("💬 Transcript is rich — using for AI metadata.")
            result = generate_metadata(ctx)
            ctx.status = "done"
        else:
            logger.warning("⚠️ Transcript is weak — skipping AI metadata generation.")
            raise RuntimeError("Output is weak. Needs user fine-tuning.")
    else:
        result = generate_metadata(ctx)

    output["title"] = result["title"]
    output["description"] = result["description"]
    output["overlay_text_primary"] = result["overlay_text_primary"]
    output["overlay_text_secondary"] = result["overlay_text_secondary"]
    output["summary"] = result["summary"]

    logger.info("📦 Metadata generation complete.")
