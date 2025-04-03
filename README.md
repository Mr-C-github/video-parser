B站视频解析下载工具
项目简介
一个无需登录即可解析和下载B站视频的工具，支持多清晰度选择，解决403 Forbidden问题。复刻了feiyudo.com的核心功能。

功能特性
✅ 无需登录获取SESSDATA

✅ 支持B站视频解析（包括短链接）

✅ 多清晰度选择（360P/480P/720P/1080P等）

✅ 解决403 Forbidden下载问题

✅ 支持批量解析下载

✅ 完善的错误处理和重试机制

快速开始
安装依赖
bash
复制
pip install -r requirements.txt
安装FFmpeg（用于m3u8下载）
Windows: 下载并添加到PATH FFmpeg官网

Mac: brew install ffmpeg

Linux: sudo apt install ffmpeg

使用示例
bash
复制
# 下载单个视频（默认最高清晰度）
python main.py "https://www.bilibili.com/video/BV1GJ411x7h7"

# 指定清晰度（720P）
python main.py "https://www.bilibili.com/video/BV1GJ411x7h7" -q 64
项目结构
复制
feiyudo-clone/
├── app.py                # Flask主应用
├── config.py             # 配置文件
├── requirements.txt      # 依赖文件
├── core/
│   ├── downloader.py     # 下载器实现
│   └── parsers/
│       └── bilibili.py   # B站解析器
└── main.py               # 命令行入口
技术实现
解决403 Forbidden的关键技术
完善的请求头设置：

自动添加Referer和User-Agent

模拟浏览器请求

B站API逆向工程：

使用官方API获取视频信息

处理短链接跳转

多清晰度支持

下载增强：

支持headers传递

自动重试机制

下载限速选项

高级用法
批量下载
python
复制
# 批量解析下载示例
urls = [
    "https://www.bilibili.com/video/BV1GJ411x7h7",
    "https://b23.tv/abc123"
]

downloader = VideoDownloader()
for url in urls:
    try:
        video_info = parser.parse(url)
        downloader.download(video_info['downloads'][0], video_info['title'])
    except Exception as e:
        print(f"下载失败: {str(e)}")
使用代理
在.env文件中添加：

ini
复制
HTTP_PROXY=http://127.0.0.1:1080
HTTPS_PROXY=http://127.0.0.1:1080
常见问题
Q: 为什么还是遇到403错误？
A: 尝试以下解决方案：

更新User-Agent

添加更多请求头（如Origin）

使用代理IP

降低请求频率

Q: 如何下载大会员专属视频？
A: 目前公共API无法下载大会员专属内容，需要登录账号获取SESSDATA。

免责声明
本项目仅用于学习和技术研究，请勿用于商业用途。使用本工具下载视频请遵守B站的相关规定。
