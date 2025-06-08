import os
import threading

from pipeline import JobContext, PIPELINE_DEFINITIONS, STEP_REGISTRY
from util import logger, watchdog, notify, shutdown_pod
from util.fetch_input_payload import fetch_input_payload


def run_pipeline():
    job_id = os.getenv("JOB_ID")
    if not job_id:
        raise RuntimeError("Missing JOB_ID")
    is_dev = os.getenv("IS_DEV", "false").lower() == "true"

    payload = fetch_input_payload(job_id, is_dev)

    ctx = JobContext(
        job_id=job_id,
        is_dev=is_dev,
        output_dir="output",
        webhook_url=os.getenv("WEBHOOK_URL"),
        input=payload
    )

    threading.Thread(target=watchdog, args=(1800, ctx), daemon=True).start()

    logger.info(f"🚀 Running pipeline for job: {ctx.job_id} - {ctx.input.get('video_url')}")

    pipeline_steps = PIPELINE_DEFINITIONS.get(ctx.input.get("mode"), [])
    if not pipeline_steps:
        logger.error(f"No pipeline defined for mode '{ctx.input.get('mode')}'")
        return ctx

    for step_name in pipeline_steps:
        step_fn = STEP_REGISTRY.get(step_name)
        if not step_fn:
            logger.error(f"Step '{step_name}' not found in registry")
            continue

        try:
            step_fn(ctx)
        except Exception as e:
            logger.error(f"❌ Pipeline step '{step_name}' failed with error: {e}")
            shutdown_pod()
            break

    logger.info(f"🏁 Pipeline complete. Final status: {ctx.status}")

    if ctx.status != "error":
        notify(ctx, "done", "done")

    shutdown_pod()
    return ctx
