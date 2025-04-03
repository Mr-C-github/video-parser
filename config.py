import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 基础配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')

# 确保下载目录存在
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 代理设置
PROXIES = {
    'http': os.getenv('HTTP_PROXY'),
    'https': os.getenv('HTTPS_PROXY')
} if os.getenv('HTTP_PROXY') else None

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br'
}

# 支持的网站
SUPPORTED_SITES = ['douyin', 'kuaishou', 'bilibili', 'youtube']

# Flask配置
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    DOWNLOAD_FOLDER = DOWNLOAD_DIR