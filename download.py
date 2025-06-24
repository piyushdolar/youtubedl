import subprocess
import json
import logging
import re
from rich.progress import Progress
from rich.console import Console

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Regex patterns to identify YouTube video and playlist URLs
VIDEO_URL_PATTERN = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]+"
)
PLAYLIST_URL_PATTERN = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/playlist\?list=|youtu\.be/playlist\?list=)[\w-]+"
)

console = Console()


def get_playlist_info(playlist_url):
    """Fetches playlist info and returns the number of videos and their URLs."""
    try:
        command = ["yt-dlp", "--flat-playlist", "--dump-json", playlist_url]
        output = subprocess.check_output(command, text=True)
        videos = json.loads(output)
        if isinstance(videos, list):
            return len(videos), [video["url"] for video in videos]
        else:
            logging.error(f"Unexpected response format: {output}")
            return 0, []
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse playlist info: {e}")
        return 0, []
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to fetch playlist info: {e}")
        return 0, []


def extract_playlist_from_video_url(url):
    """Extracts playlist ID from a video URL if present."""
    match = re.search(r"list=([\w-]+)", url)
    if match:
        return f"https://www.youtube.com/playlist?list={match.group(1)}"
    return None


def download_youtube_url(url):
    """Downloads audio from a YouTube video or playlist."""
    if VIDEO_URL_PATTERN.match(url):
        logging.info(f"Detected YouTube video URL: {url}")
        playlist_url = extract_playlist_from_video_url(url)
        if playlist_url:
            logging.info(f"Detected playlist URL within video URL: {playlist_url}")
            confirm = input(
                "This is a YouTube video URL with an embedded playlist. Do you want to download audio from this playlist? (y/n): "
            )
            if confirm.lower() == "y":
                return download_playlist(playlist_url)
            else:
                logging.info(f"Skipping download for: {url}")
                return False
        else:
            confirm = input(
                "This is a YouTube video URL. Do you want to download audio from this video? (y/n): "
            )
            if confirm.lower() == "y":
                return download_video(url)
            else:
                logging.info(f"Skipping download for: {url}")
                return False

    elif PLAYLIST_URL_PATTERN.match(url):
        logging.info(f"Detected YouTube playlist URL: {url}")
        confirm = input(
            "This is a YouTube playlist URL. Do you want to download audio from this playlist? (y/n): "
        )
        if confirm.lower() == "y":
            return download_playlist(url)
        else:
            logging.info(f"Skipping download for: {url}")
            return False

    else:
        logging.error(f"Invalid YouTube URL: {url}")
        return False


def download_video(url):
    """Downloads audio from a single YouTube video."""
    try:
        command = [
            "yt-dlp",
            "-f",
            "bestaudio",
            "--extract-audio",
            "--audio-quality",
            "0",
            "--audio-format",
            "mp3",
            "--embed-metadata",
            "--add-metadata",
            "-o",
            "%(title)s.%(ext)s",
            url,
        ]
        logging.info(f"Starting download for: {url}")
        subprocess.run(command, check=True)
        logging.info(f"Successfully downloaded: {url}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to download {url}: {e}")
        return False


def download_playlist(url):
    """Downloads audio from all videos in a YouTube playlist."""
    total_videos, video_urls = get_playlist_info(url)
    if total_videos == 0:
        logging.error(f"No videos found in playlist: {url}")
        return False

    logging.info(f"Playlist contains {total_videos} videos.")
    downloaded_count = 0

    with Progress() as progress:
        task = progress.add_task("Downloading playlist...", total=total_videos)
        for video_url in video_urls:
            if download_video(video_url):
                downloaded_count += 1
            progress.update(task, advance=1)

    logging.info(f"Downloaded {downloaded_count} out of {total_videos} videos.")
    return True


if __name__ == "__main__":
    urls = input(
        "Enter the URLs of the YouTube videos or playlists separated by commas: "
    ).split(",")
    for url in urls:
        download_youtube_url(url.strip())
