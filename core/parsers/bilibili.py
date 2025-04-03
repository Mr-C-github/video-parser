from .base_parser import BaseParser
import re
import json

class BilibiliParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.headers.update({
            'Referer': 'https://www.bilibili.com/',
        })
        self.quality_map = {
            16: '360P',
            32: '480P',
            64: '720P',
            74: '720P60',
            80: '1080P',
            112: '1080P+',
            116: '1080P60',
            120: '4K'
        }

    def parse(self, url):
        # 解析短链接
        if 'b23.tv' in url:
            url = self._resolve_short_url(url)

        bvid = self._extract_bvid(url)
        if not bvid:
            raise Exception('无法从URL中提取视频BV号')

        # 获取视频信息
        return self._get_video_info(bvid)

    def _extract_bvid(self, url):
        patterns = [
            r'/video/(BV\w+)',
            r'BV\w+'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def _get_video_info(self, bvid):
        # 获取视频基本信息
        info_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        info_data = self._get_json(info_url)

        if info_data.get('code') != 0:
            raise Exception(info_data.get('message', '获取视频信息失败'))

        video_info = info_data['data']
        cid = video_info['cid']

        # 获取视频播放地址
        play_url = f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn=80&fnval=16"
        play_data = self._get_json(play_url)

        if play_data.get('code') != 0:
            raise Exception(play_data.get('message', '获取播放地址失败'))

        # 提取不同清晰度的视频
        qualities = []
        accept_quality = play_data['data'].get('accept_quality', [])

        for qn in accept_quality:
            quality_url = f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn={qn}"
            quality_data = self._get_json(quality_url)

            if quality_data.get('code') == 0 and quality_data['data']['durl']:
                video_url = quality_data['data']['durl'][0]['url']
                qualities.append({
                    'quality': self.quality_map.get(qn, f'未知{qn}'),
                    'url': video_url,
                    'type': 'mp4',
                    'size': round(quality_data['data']['durl'][0]['size'] / (1024 * 1024), 1)
                })

        # 如果没有获取到任何质量，尝试默认URL
        if not qualities and play_data['data']['durl']:
            qualities.append({
                'quality': '默认',
                'url': play_data['data']['durl'][0]['url'],
                'type': 'mp4',
                'size': round(play_data['data']['durl'][0]['size'] / (1024 * 1024), 1)
            })

        return {
            'title': video_info['title'],
            'cover': video_info['pic'],
            'author': video_info['owner']['name'],
            'duration': video_info['duration'],
            'downloads': qualities
        }