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

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 代理设置
PROXY = 'http://127.0.0.1:10900'

# 创建必要的目录
def ensure_directories():
    """确保所有必要的目录都存在"""
    directories = [
        "static",
        "static/videos",
        "templates"
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# 确保目录存在
ensure_directories()

app = FastAPI()

# 挂载静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 视频目录
VIDEOS_DIR = "static/videos"

# 存储视频信息的JSON文件
VIDEOS_INFO_FILE = "videos_info.json"

def is_valid_youtube_url(url):
    """验证是否是有效的YouTube URL"""
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
    """使用yt-dlp获取视频信息"""
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
    """同步下载视频"""
    ydl_opts = {
        'format': 'best',  # 选择最佳质量
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'verbose': True,  # 启用详细日志
        'progress': True,  # 显示进度
        'ignoreerrors': False,  # 不忽略错误
        'no_warnings': False,  # 显示警告
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
        
        # 获取视频信息
        info = get_video_info(url)
        logger.info(f"Video info: {info}")
        
        # 使用线程池执行下载
        try:
            await asyncio.to_thread(download_video_sync, url, output_dir)
        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
        
        # 获取下载的文件
        files = os.listdir(output_dir)
        if not files:
            logger.error("No files found in output directory after download")
            raise HTTPException(status_code=500, detail="No files found after download")
        
        video_file = files[0]
        file_path = f'{output_dir}/{video_file}'
        logger.info(f"Download completed: {file_path}")
        
        # 保存视频信息
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