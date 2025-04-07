import re
import json
import time
import random
import hashlib
from urllib.parse import unquote, urlparse, parse_qs
import requests
from fake_useragent import UserAgent

class DouyinParser:
    def __init__(self, proxy=None):
        self.session = requests.Session()
        self.proxy = proxy
        self.ua = UserAgent()

        if proxy:
            self.session.proxies = {
                'http': proxy,
                'https': proxy
            }

        self.headers = {
            'User-Agent': self.ua.chrome,
            'Referer': 'https://www.douyin.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Cookie': self._generate_cookie()
        }

        self.api_url = "https://www.douyin.com/aweme/v1/web/aweme/detail/"
        self.retry_count = 3
        self.xbogus_cache = {}

    def _generate_cookie(self):
        """生成随机Cookie"""
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        return (
            f"s_v_web_id=verify_{''.join(random.choices(chars, k=16))}; "
            f"ttwid=1%7C{''.join(random.choices(chars, k=32))}; "
            f"msToken={''.join(random.choices(chars, k=32))}; "
            f"__ac_nonce={''.join(random.choices(chars, k=21))}; "
            f"__ac_signature={''.join(random.choices(chars, k=40))}"
        )

    def parse(self, url):
        """主解析方法"""
        try:
            # 1. 解析短链接
            final_url = self._resolve_short_url(url)
            print(f"[DEBUG] 最终URL: {final_url}")

            # 2. 提取视频ID
            video_id = self._extract_video_id(final_url) or self._extract_video_id(url)
            if not video_id:
                raise Exception("无法提取视频ID")
            print(f"[DEBUG] 视频ID: {video_id}")

            # 3. 获取视频信息
            return self._get_video_info(video_id)

        except Exception as e:
            raise Exception(f"解析失败: {str(e)}")

    def _resolve_short_url(self, url):
        """解析短链接（带反爬处理）"""
        if 'v.douyin.com' not in url and 'iesdouyin.com' not in url:
            return url

        try:
            time.sleep(random.uniform(1.5, 3.0))
            self.headers['User-Agent'] = self.ua.chrome

            # 先尝试HEAD方法
            resp = self.session.head(
                url,
                headers=self.headers,
                allow_redirects=True,
                timeout=10
            )

            if resp.url != url:
                return resp.url

            # HEAD失败则尝试GET
            resp = self.session.get(
                url,
                headers=self.headers,
                allow_redirects=False,
                timeout=10
            )

            if resp.status_code in (301, 302):
                return resp.headers.get('Location', url)

        except Exception as e:
            print(f"[WARNING] 短链接解析失败: {str(e)}")

        return url

    def _extract_video_id(self, url):
        """增强版ID提取"""
        url = unquote(url)

        # 处理嵌套URL
        parsed = urlparse(url)
        if parsed.query:
            params = parse_qs(parsed.query)
            if 'page_url' in params:
                return self._extract_video_id(params['page_url'][0])
            for key in ['video_id', 'item_id', 'id', 'aweme_id']:
                if key in params and params[key][0].isdigit():
                    return params[key][0]

        # 从路径提取
        path = parsed.path
        patterns = [
            r'/video/(\d{10,})',
            r'/share/video/(\d+)',
            r'/(\d{19})',
            r'/note/(\d+)',
            r'/v\.douyin\.com/\w+/(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, path)
            if match and match.group(1).isdigit():
                return match.group(1)

        return None

    def _get_video_info(self, video_id):
        """获取视频信息（带完整反爬措施）"""
        params = {
            'aweme_id': video_id,
            'aid': 6383,
            'device_platform': 'web',
            'version_code': '190500',
            'X-Bogus': self._generate_xbogus(video_id),
            '_signature': self._generate_signature()
        }

        for attempt in range(self.retry_count):
            try:
                time.sleep(random.uniform(2.0, 5.0))
                self.headers.update({
                    'User-Agent': self.ua.chrome,
                    'Cookie': self._generate_cookie()
                })

                response = self.session.get(
                    self.api_url,
                    params=params,
                    headers=self.headers,
                    timeout=15
                )

                print(f"[DEBUG] 响应状态码: {response.status_code}")
                print(f"[DEBUG] 响应内容: {response.text[:200]}...")

                if response.status_code == 403:
                    raise Exception("触发反爬(403)，请更换IP或Cookie")

                if not response.text.strip():
                    raise Exception("空响应内容")

                data = response.json()

                if not data.get('aweme_detail'):
                    if data.get('status_code') == 8:
                        raise Exception("视频不存在或已删除")
                    raise Exception("无效的响应数据")

                return self._format_result(data['aweme_detail'])

            except json.JSONDecodeError:
                error_msg = f"JSON解析失败（尝试 {attempt+1}/{self.retry_count}）"
                print(f"[ERROR] {error_msg}")
                if attempt == self.retry_count - 1:
                    raise Exception(f"获取视频信息失败: 无效的JSON响应")
                continue

            except Exception as e:
                print(f"[ERROR] 请求失败（尝试 {attempt+1}/{self.retry_count}）: {str(e)}")
                if attempt == self.retry_count - 1:
                    raise Exception(f"获取视频信息失败: {str(e)}")
                continue

    def _generate_xbogus(self, aweme_id):
        """生成X-Bogus签名（生产环境需完整实现）"""
        param_str = f"aweme_id={aweme_id}&device_platform=web&aid=6383"
        return f"DFSz{hashlib.md5(param_str.encode()).hexdigest()[:8]}swVY{random.randint(1000,9999)}"

    def _generate_signature(self):
        """生成签名（生产环境需完整实现）"""
        return f"v2_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:40]}"

    def _format_result(self, item):
        """格式化结果"""
        video = item.get('video', {})
        play_addr = video.get('play_addr', {})

        return {
            'id': item.get('aweme_id'),
            'title': item.get('desc', '抖音视频')[:100],
            'cover': video.get('cover', {}).get('url_list', [''])[0],
            'author': item.get('author', {}).get('nickname', '未知用户'),
            'duration': video.get('duration', 0) // 1000,
            'downloads': [
                {
                    'quality': '无水印',
                    'url': self._get_no_watermark_url(play_addr.get('uri')),
                    'type': 'mp4'
                },
                {
                    'quality': '高清',
                    'url': play_addr.get('url_list', [''])[0],
                    'type': 'mp4'
                }
            ]
        }

    def _get_no_watermark_url(self, uri):
        """获取无水印URL"""
        if not uri:
            return None
        return f"https://aweme.snssdk.com/aweme/v1/play/?video_id={uri}&ratio=720p"


# 使用示例
if __name__ == "__main__":
    # 测试URL（包含嵌套page_url的特殊格式）
    test_url = "https://www.douyin.com/?enter_recommend_method=item_non_existent_recommend_click&page_url=https%3A%2F%2Fwww.douyin.com%2Fvideo%2F7152430285123947813&recommend=1"

    # 初始化解析器（可传入代理）
    parser = DouyinParser(proxy=None)  # 示例：proxy='http://127.0.0.1:8888'

    try:
        print(f"\n开始解析URL: {test_url}")
        result = parser.parse(test_url)

        print("\n解析成功！")
        print(f"视频标题: {result['title']}")
        print(f"视频作者: {result['author']}")
        print("下载链接:")
        for download in result['downloads']:
            if download:
                print(f"- [{download['quality']}] {download['url']}")

    except Exception as e:
        print(f"\n解析失败: {str(e)}")

    finally:
        parser.session.close()