from pipeline import JobContext, PIPELINE_DEFINITIONS, STEP_REGISTRY
from util import logger, notify
from util.fetch_input_payload import fetch_input_payload


def run_pipeline(job):
    is_dev = False
    job_input = job["input"]
    job_id = job_input["job_id"]
    webhook_url = job_input["webhook_url"]

    if not job_id:
        raise RuntimeError("Job id is missing")

    payload = fetch_input_payload(job_id, webhook_url)

    ctx = JobContext(
        job_id=job_id,
        is_dev=is_dev,
        output_dir="output",
        webhook_url=webhook_url,
        input=payload
    )

    logger.info(f"🚀 Running pipeline for job: {ctx.job_id} - {ctx.input.get('video_url')}")

    pipeline_steps = PIPELINE_DEFINITIONS.get(ctx.input.get("mode"), [])
    if not pipeline_steps:
        logger.error(f"No pipeline defined for mode '{ctx.input.get('mode')}'")
        raise RuntimeError("No pipeline defined")

    for step_name in pipeline_steps:
        step_fn = STEP_REGISTRY.get(step_name)
        if not step_fn:
            logger.error(f"Step '{step_name}' not found in registry")
            raise RuntimeError("Step not found in registry")

        try:
            step_fn(ctx)
        except Exception as e:
            logger.error(f"❌ Pipeline step '{step_name}' failed with error: {e}")
            raise

    logger.info(f"🏁 Pipeline complete. Final status: {ctx.status}")

    if ctx.status != "error":
        notify(ctx, "done", "done")

    return ctx
