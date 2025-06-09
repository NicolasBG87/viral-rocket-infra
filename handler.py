import runpod

from pipeline.run import run_pipeline
from util import logger

output_dir = "output"


def handler(job):
    try:
        result = run_pipeline(job)
        return result
    except Exception as e:
        logger.exception(str(e))
        return {'error': str(e)}


runpod.serverless.start({"handler": handler})
