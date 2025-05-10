class ProcessingError(Exception):
    def __init__(self, step: str, job_id: str, status: str, stage: str, message: str):
        self.step = step
        self.job_id = job_id
        self.status = status
        self.stage = stage
        super().__init__(f"[Step Failed]: {step}")
