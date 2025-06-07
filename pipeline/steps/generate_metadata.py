from pipeline import JobContext, step
from modules.metadata.generator import generate_metadata
from util import logger


@step("generate_metadata")
def run(ctx: JobContext):
    output = ctx.output
    score = output.get("video_metadata").get("transcript_score", 0)
    transcript = output.get("video_metadata").get("transcript")
    if not transcript:
        raise RuntimeError("No transcript available for metadata generation")

    if score >= 0.5:
        logger.info("💬 Transcript is rich — using for GPT metadata.")
        result = generate_metadata(ctx)
        ctx.status = "done"
    else:
        logger.warning("⚠️ Transcript is weak — skipping GPT metadata generation.")
        raise RuntimeError("Output is weak. Needs user fine-tuning.")

    output["title"] = result["title"]
    output["description"] = result["description"]
    output["summary"] = result["summary"]

    logger.info("📦 Metadata generation complete.")
