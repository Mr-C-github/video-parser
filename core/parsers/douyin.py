from .base_parser import BaseParser
import re
import json
from urllib.parse import unquote

class DouyinParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.headers.update({
            'Referer': 'https://www.douyin.com/',
        })

    def parse(self, url):
        # 解析短链接
        if 'v.douyin.com' in url:
            url = self._resolve_short_url(url)

        video_id = self._extract_video_id(url)
        if not video_id:
            raise Exception('无法从URL中提取视频ID')

        # 获取视频信息
        return self._get_video_info(video_id)

    def _extract_video_id(self, url):
        patterns = [
            r'/video/(\d+)',
            r'/share/video/(\d+)',
            r'video/(\d+)',
            r'video_id=(\d+)',
            r'item_id=(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def _get_video_info(self, video_id):
        # 获取视频信息API
        api_url = "https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/"
        params = {
            'item_ids': video_id
        }

        data = self._get_json(api_url, params=params)

        if not data.get('item_list'):
            raise Exception('获取视频信息失败')

        item = data['item_list'][0]

        # 获取无水印视频
        no_watermark_url = self._get_no_watermark_url(item)

        # 获取有水印视频
        watermark_url = item['video']['play_addr']['url_list'][0]

        return {
            'title': item['desc'] or '抖音视频',
            'cover': item['video']['cover']['url_list'][0],
            'author': item['author']['nickname'],
            'duration': item['video']['duration'] // 1000,  # 转换为秒
            'downloads': [
                {
                    'quality': '无水印',
                    'url': no_watermark_url,
                    'type': 'mp4',
                    'size': self._estimate_size(item['video']['play_addr']['width'],
                                                item['video']['play_addr']['height'])
                },
                {
                    'quality': '有水印',
                    'url': watermark_url,
                    'type': 'mp4',
                    'size': self._estimate_size(item['video']['play_addr']['width'],
                                                item['video']['play_addr']['height'])
                }
            ]
        }

    def _get_no_watermark_url(self, item):
        """获取无水印视频URL"""
        uri = item['video']['play_addr']['uri']
        no_wm_url = f"https://aweme.snssdk.com/aweme/v1/play/?video_id={uri}&ratio=720p&line=0"
        return no_wm_url

    def _estimate_size(self, width, height):
        """估算视频大小"""
        # 简单的估算公式 (MB)
        return round(width * height * 0.0000015, 1)