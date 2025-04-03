import requests
from urllib.parse import urlparse
import re
import json

class BaseParser:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def parse(self, url):
        """解析视频信息，返回字典"""
        raise NotImplementedError

    def _extract_video_id(self, url):
        """从URL中提取视频ID"""
        raise NotImplementedError

    def _get_html(self, url, params=None):
        """获取网页内容"""
        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            raise Exception(f"请求失败: {str(e)}")

    def _get_json(self, url, params=None):
        """获取JSON数据"""
        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            raise Exception(f"获取JSON失败: {str(e)}")

    def _resolve_short_url(self, url):
        """解析短链接"""
        try:
            resp = self.session.head(url, allow_redirects=True, timeout=5)
            return resp.url
        except requests.RequestException:
            return url