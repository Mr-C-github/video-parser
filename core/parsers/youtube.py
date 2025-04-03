from .base_parser import BaseParser
import re
import json
from urllib.parse import parse_qs, urlparse

class YouTubeParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.headers.update({
            'Referer': 'https://www.youtube.com/',
        })

    def parse(self, url):
        # 解析短链接
        if 'youtu.be' in url:
            url = self._resolve_short_url(url)

        video_id = self._extract_video_id(url)
        if not video_id:
            raise Exception('无法从URL中提取视频ID')

        return self._get_video_info(video_id)

    def _extract_video_id(self, url):
        patterns = [
            r'v=([\w-]+)',  # 常规URL
            r'youtu\.be/([\w-]+)',  # 短链接
            r'embed/([\w-]+)',  # 嵌入代码
            r'/([\w-]{11})$'  # 直接11位ID
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def _get_video_info(self, video_id):
        # 获取视频信息
        embed_url = f"https://www.youtube.com/embed/{video_id}"
        html = self._get_html(embed_url)

        # 从嵌入页面提取信息
        title = self._extract_title(html)
        if not title:
            raise Exception('无法获取视频标题')

        # 构造下载链接
        download_url = f"https://www.youtube.com/watch?v={video_id}"

        return {
            'title': title,
            'cover': f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            'author': 'YouTube视频',
            'downloads': [
                {
                    'quality': '高清',
                    'url': download_url,
                    'type': 'mp4',
                    'size': None  # YouTube需要额外处理获取大小
                }
            ]
        }

    def _extract_initial_data(self, html):
        """从HTML中提取初始数据"""
        pattern = r'var ytInitialData = (.*?);</script>'
        match = re.search(pattern, html)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
        return None

    def _extract_title(self, html):
        """从HTML中提取视频标题"""
        pattern = r'<title>(.*?)</title>'
        match = re.search(pattern, html)
        if match:
            title = match.group(1)
            return title.replace(' - YouTube', '').strip()
        return None