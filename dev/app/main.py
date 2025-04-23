from dev.app.logger import benchmark_start, benchmark_stop
from dev.app.modules.downloader import download_video


def main():
    process_start = benchmark_start("[1] Processing started...")

    start = benchmark_start("[2] Downloading video started...")
    url = "https://www.youtube.com/watch?v=D_5r45LipuM"
    download_result = download_video(url)
    video_path = download_result["path"]
    benchmark_stop("[2] Downloading video", start)

    benchmark_stop('Processing', process_start)
