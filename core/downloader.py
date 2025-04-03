import os
import subprocess
import requests
from tqdm import tqdm
from urllib.parse import unquote
from datetime import datetime
import re

class VideoDownloader:
    def __init__(self, download_dir='downloads'):
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)

    def download(self, url, title, format='mp4'):
        """下载视频文件"""
        # 清理文件名
        title = self._clean_filename(title)
        filename = f"{title}.{format}"
        filepath = os.path.join(self.download_dir, filename)

        # 如果文件已存在，添加时间戳
        if os.path.exists(filepath):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{title}_{timestamp}.{format}"
            filepath = os.path.join(self.download_dir, filename)

        # 处理m3u8格式
        if 'm3u8' in url:
            return self._download_m3u8(url, filepath)

        # 直接下载视频文件
        return self._download_direct(url, filepath)

    def _download_m3u8(self, m3u8_url, output_path):
        """下载m3u8格式视频"""
        try:
            cmd = [
                'ffmpeg',
                '-i', m3u8_url,
                '-c', 'copy',
                '-bsf:a', 'aac_adtstoasc',
                output_path
            ]
            subprocess.run(cmd, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            raise Exception(f"m3u8下载失败: {str(e)}")
        except FileNotFoundError:
            raise Exception("请先安装FFmpeg并添加到系统PATH")

    def _download_direct(self, url, output_path):
        """直接下载视频文件"""
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))

                with open(output_path, 'wb') as f, tqdm(
                        desc=os.path.basename(output_path),
                        total=total_size,
                        unit='iB',
                        unit_scale=True,
                        unit_divisor=1024,
                ) as bar:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:  # 过滤保持活动的块
                            size = f.write(chunk)
                            bar.update(size)

            return output_path
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise Exception(f"下载失败: {str(e)}")

    def _clean_filename(self, filename):
        """清理文件名中的非法字符"""
        # 移除特殊字符
        filename = re.sub(r'[\\/*?:"<>|]', '', filename)
        # 缩短过长文件名
        if len(filename) > 100:
            filename = filename[:50] + '...' + filename[-50:]
        return filename.strip()