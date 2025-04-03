from .base_parser import BaseParser
import re
import json
from urllib.parse import unquote

class KuaishouParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.headers.update({
            'Referer': 'https://www.kuaishou.com/',
            'Cookie': 'did=web_xxxxxxxx'  # 可能需要有效的cookie
        })

    def parse(self, url):
        # 解析短链接
        if 'gifshow.com' in url or 'v.kuaishou' in url:
            url = self._resolve_short_url(url)

        video_id = self._extract_video_id(url)
        if not video_id:
            raise Exception('无法从URL中提取视频ID')

        return self._get_video_info(video_id)

    def _extract_video_id(self, url):
        patterns = [
            r'/short-video/(\w+)',
            r'photo/(\w+)',
            r'video/(\w+)',
            r'vid=(\w+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def _get_video_info(self, video_id):
        # 快手需要先获取页面内容提取初始数据
        page_url = f"https://www.kuaishou.com/short-video/{video_id}"
        html = self._get_html(page_url)

        # 从页面中提取初始数据
        initial_data = self._extract_initial_data(html)
        if not initial_data:
            raise Exception('无法提取视频初始数据')

        # 获取视频信息
        video_info = initial_data.get('video', {})
        author_info = initial_data.get('author', {})

        # 获取无水印视频
        no_watermark_url = self._get_no_watermark_url(video_info)

        return {
            'title': video_info.get('caption', '快手视频'),
            'cover': video_info.get('coverUrl', ''),
            'author': author_info.get('name', '未知作者'),
            'duration': video_info.get('duration', 0) / 1000,  # 转换为秒
            'downloads': [
                {
                    'quality': '无水印',
                    'url': no_watermark_url,
                    'type': 'mp4',
                    'size': self._estimate_size(video_info.get('width', 720),
                                                video_info.get('height', 1280))
                }
            ]
        }

    def _extract_initial_data(self, html):
        """从HTML中提取初始数据"""
        pattern = r'<script>window\.__INITIAL_STATE__=(.*?);\(function'
        match = re.search(pattern, html)
        if match:
            try:
                return json.loads(unquote(match.group(1)))
            except json.JSONDecodeError:
                return None
        return None

    def _get_no_watermark_url(self, video_info):
        """获取无水印视频URL"""
        # 快手无水印视频需要从playUrls中提取
        play_urls = video_info.get('playUrls', [])
        if play_urls:
            return play_urls[0].get('url', '')
        return ''

    def _estimate_size(self, width, height):
        """估算视频大小(MB)"""
        return round(width * height * 0.000002, 1)