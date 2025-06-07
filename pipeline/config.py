PIPELINE_DEFINITIONS = {
    "standard": [
        "download",
        "check_limits",
        "transcribe",
        "transcript_score",
        "generate_metadata",
        "save_output",
    ],
    "user_enhanced": [
        "generate_metadata",
    ]
}
