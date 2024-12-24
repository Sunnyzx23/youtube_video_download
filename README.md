# YouTube Video Downloader

一个简单的YouTube视频下载器，基于FastAPI和yt-dlp构建。支持视频信息获取、下载和本地管理功能。

## 功能特点

- 支持输入YouTube视频链接进行下载
- 异步下载处理，避免阻塞
- 显示下载进度
- 视频信息展示（标题、时长、作者等）
- 本地视频管理和预览
- 响应式界面设计

## 技术栈

- FastAPI - Web框架
- yt-dlp - 视频下载核心
- Jinja2 - 模板引擎
- TailwindCSS - 样式框架
- Python 3.10+

## 安装步骤

1. 克隆项目： 
bash
git clone https://github.com/Sunnyzx23/youtube_video_download.git
cd youtube_video_download

2. 安装依赖：
```bash
pip3 install fastapi uvicorn python-multipart yt-dlp jinja2
```

3. 创建必要的目录：
```bash
mkdir -p static/videos
mkdir templates
```

## 使用说明

1. 启动服务器：
```bash
uvicorn main:app --reload
```

2. 访问网页：
   - 打开浏览器访问 http://localhost:8000
   - 在输入框中粘贴YouTube视频链接
   - 点击下载按钮开始下载
   - 下载完成后可在页面下方查看和预览视频

## 项目结构
README.md
youtube_video_downloader/
├── main.py # FastAPI后端代码
├── templates/
│ └── index.html # 前端页面模板
├── static/
│ └── videos/ # 下载的视频存储目录
└── README.md # 项目说明文档

## 注意事项

- 确保有足够的磁盘空间存储下载的视频
- 需要稳定的网络连接
- 如果在中国大陆使用，可能需要配置代理
- 仅供学习和个人使用，请遵守相关法律法规
- 建议定期清理不需要的视频文件

## 代理设置

如果需要使用代理，可以在 `main.py` 中设置：
```python
PROXY = 'http://your-proxy-address:port'
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 作者

[Sunnyzx23](https://github.com/Sunnyzx23)