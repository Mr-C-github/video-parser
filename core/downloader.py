import os
import yt_dlp
from browser_cookie3 import chrome
import requests  # 替换 pyhttpx

class VideoDownloader:
    def __init__(self, download_dir='downloads'):
        self.download_dir = os.path.abspath(download_dir)
        os.makedirs(self.download_dir, exist_ok=True)

        # 自动获取浏览器cookies
        self.cookies = self._get_browser_cookies()

        # 创建会话（使用标准requests替换pyhttpx）
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.bilibili.com'
        })

        # 如果有cookies则添加到会话
        if self.cookies:
            self.session.cookies.update({c.name: c.value for c in self.cookies})

    def download(self, url, title=None):
        """终极下载方法"""
        try:
            # 方案1：优先使用yt-dlp+浏览器cookies
            try:
                return self._ytdlp_download(url)
            except Exception as e:
                print(f"yt-dlp失败，尝试备用方案: {str(e)}")

            # 方案2：使用会话直连下载
            return self._direct_download(url, title)

        except Exception as e:
            raise Exception(f"所有方案均失败: {str(e)}")

    def _ytdlp_download(self, url):
        """yt-dlp终极配置"""
        ydl_opts = {
            'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'cookiefile': self._export_cookies(),
            'extractor_args': {
                'bilibili': {
                    'skip_dash': True,
                    'format_sort': ['flv']
                }
            },
            'http_headers': {
                'Referer': 'https://www.bilibili.com',
                'X-Forwarded-For': self._generate_random_ip()
            },
            'throttledratelimit': 102400,  # 限速伪装
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

    def _direct_download(self, url, title):
        """流式传输文件到客户端"""
        try:
            # 获取真实下载地址
            real_url = self._get_real_url(url)

            # 发起流式请求
            resp = self.session.get(real_url, stream=True, timeout=30)
            resp.raise_for_status()

            # 生成安全文件名
            filename = self._generate_filename(title or os.path.basename(url))

            # 创建生成器函数
            def generate():
                chunk_size = 1024 * 1024  # 1MB/chunk
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if chunk:
                        yield chunk

            # 返回流式响应
            return {
                'filename': filename,
                'stream': generate(),
                'content_type': resp.headers.get('Content-Type', 'application/octet-stream'),
                'content_length': resp.headers.get('Content-Length')
            }

        except Exception as e:
            raise Exception(f"流式传输失败: {str(e)}")

    # ----------- 关键辅助方法 -----------
    def _get_browser_cookies(self):
        """获取浏览器所有cookies"""
        try:
            return chrome(domain_name='bilibili.com')
        except:
            return {}

    def _export_cookies(self):
        """导出为yt-dlp可用的cookies文件"""
        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile(mode='w+', delete=False) as f:
            for cookie in self.cookies:
                f.write(f"{cookie.domain}\tTRUE\t{cookie.path}\t{'TRUE' if cookie.secure else 'FALSE'}\t{cookie.expires or '0'}\t{cookie.name}\t{cookie.value}\n")
            return f.name

    def _generate_random_ip(self):
        """生成随机国内IP"""
        import random
        return f"116.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"

    def _get_real_url(self, url):
        """解析真实下载地址（绕过CDN）"""
        # 此处需要根据目标网站实现，示例为B站逻辑
        if 'bilibili' in url:
            try:
                resp = self.session.get(url)
                return resp.json()['data']['durl'][0]['url']
            except:
                return url
        return url

    def _generate_filename(self, title):
        """生成安全文件名"""
        import re
        filename = re.sub(r'[\\/*?:"<>|]', '', title)[:100]
        return f"{filename}.mp4"