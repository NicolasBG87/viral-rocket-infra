PIPELINE_DEFINITIONS = {
    "standard": [
        "download",
        "check_limits",
        "transcribe",
        "transcript_score",
        "generate_metadata",
        "generate_thumbnail",
        "save_output",
    ],
    "user_enhanced": [
        "generate_metadata",
        "generate_thumbnail",
    ],
    "test_thumb_gen": [
        "generate_thumbnail",
    ]
}
