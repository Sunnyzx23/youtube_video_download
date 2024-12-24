from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import yt_dlp
import json
import os
import asyncio
import uuid
from datetime import datetime
import logging
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Proxy settings
PROXY = 'http://127.0.0.1:10900'

# Create necessary directories
def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        "static",
        "static/videos",
        "templates"
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Ensure directories exist
ensure_directories()

app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Video directory
VIDEOS_DIR = "static/videos"

# JSON file for storing video information
VIDEOS_INFO_FILE = "videos_info.json"

def is_valid_youtube_url(url):
    """Validate if the URL is a valid YouTube URL"""
    try:
        parsed = urllib.parse.urlparse(url)
        return ('youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc)
    except:
        return False

def load_videos_info():
    if os.path.exists(VIDEOS_INFO_FILE):
        with open(VIDEOS_INFO_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_videos_info(info):
    with open(VIDEOS_INFO_FILE, 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

def get_video_info(url):
    """Get video information using yt-dlp"""
    try:
        if not is_valid_youtube_url(url):
            raise HTTPException(status_code=400, 
                              detail="Invalid YouTube URL")

        logger.info(f"Getting info for URL: {url}")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        if PROXY:
            ydl_opts['proxy'] = PROXY
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            logger.info(f"Video info extracted: {info}")
            
            return {
                'title': info.get('title', 'Unknown Title'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown Uploader'),
                'description': info.get('description', 'No description available')
            }
            
    except Exception as e:
        logger.error(f"Error in get_video_info: {str(e)}")
        raise HTTPException(status_code=500, 
                          detail=f"Failed to get video info: {str(e)}")

def download_video_sync(url, output_dir):
    """Synchronous video download function"""
    ydl_opts = {
        'format': 'best',  # Select best quality
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'verbose': True,  # Enable verbose logging
        'progress': True,  # Show progress
        'ignoreerrors': False,  # Don't ignore errors
        'no_warnings': False,  # Show warnings
    }
    
    if PROXY:
        ydl_opts['proxy'] = PROXY
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("Starting video download...")
            error_code = ydl.download([url])
            logger.info(f"Download completed with code: {error_code}")
            if error_code != 0:
                raise Exception(f"yt-dlp returned error code: {error_code}")
    except Exception as e:
        logger.error(f"Error during download: {str(e)}")
        raise

@app.post("/download")
async def download_video(request: Request):
    try:
        form = await request.form()
        url = form.get("url")
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        logger.info(f"Starting download for URL: {url}")
        
        video_id = str(uuid.uuid4())
        output_dir = f'{VIDEOS_DIR}/{video_id}'
        os.makedirs(output_dir, exist_ok=True)
        
        # Get video information
        info = get_video_info(url)
        logger.info(f"Video info: {info}")
        
        # Use thread pool for download
        try:
            await asyncio.to_thread(download_video_sync, url, output_dir)
        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
        
        # Get downloaded file
        files = os.listdir(output_dir)
        if not files:
            logger.error("No files found in output directory after download")
            raise HTTPException(status_code=500, detail="No files found after download")
        
        video_file = files[0]
        file_path = f'{output_dir}/{video_file}'
        logger.info(f"Download completed: {file_path}")
        
        # Save video information
        video_info = {
            'id': video_id,
            'title': info['title'],
            'duration': info['duration'],
            'uploader': info['uploader'],
            'description': info['description'],
            'file_path': f'/static/videos/{video_id}/{video_file}',
            'download_date': datetime.now().isoformat(),
            'filesize': os.path.getsize(file_path),
        }
        
        videos_info = load_videos_info()
        videos_info[video_id] = video_info
        save_videos_info(videos_info)
        
        return video_info
            
    except Exception as e:
        logger.error(f"Error in download_video: {str(e)}")
        raise HTTPException(status_code=500, 
                          detail=str(e))

@app.get("/")
async def home(request: Request):
    videos = load_videos_info()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "videos": videos}
    )

@app.get("/videos")
async def list_videos():
    return load_videos_info() 