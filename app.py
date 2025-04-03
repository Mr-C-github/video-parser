from flask import Flask, render_template, request, jsonify, redirect, url_for
from core.parsers.douyin import DouyinParser
from core.parsers.kuaishou import KuaishouParser
from core.parsers.bilibili import BilibiliParser
from core.parsers.youtube import YouTubeParser
from core.downloader import VideoDownloader
import re
import os
from datetime import datetime
from urllib.parse import urlparse

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# 初始化解析器
PARSERS = {
    'douyin': DouyinParser(),
    'kuaishou': KuaishouParser(),
    'bilibili': BilibiliParser(),
    'youtube': YouTubeParser()
}

# 初始化下载器
downloader = VideoDownloader()

def detect_platform(url):
    """检测URL所属平台"""
    domain_rules = {
        'douyin': ['douyin.com', 'iesdouyin.com'],
        'kuaishou': ['kuaishou.com', 'gifshow.com'],
        'bilibili': ['bilibili.com', 'b23.tv'],
        'youtube': ['youtube.com', 'youtu.be']
    }

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    for platform, domains in domain_rules.items():
        if any(d in domain for d in domains):
            return platform
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/parse', methods=['POST'])
def parse_video():
    url = request.form.get('url', '').strip()
    if not url:
        return jsonify({'error': '请输入视频URL'}), 400

    # 自动补全http协议
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    platform = detect_platform(url)
    if not platform:
        return jsonify({'error': '不支持的视频平台'}), 400

    try:
        parser = PARSERS[platform]
        result = parser.parse(url)

        # 添加平台信息和原始URL
        result.update({
            'platform': platform,
            'original_url': url,
            'parse_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'解析失败: {str(e)}', 'platform': platform}), 500

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    if not data or 'url' not in data or 'title' not in data:
        return jsonify({'error': '缺少必要参数'}), 400

    try:
        # 清理文件名中的非法字符
        title = re.sub(r'[\\/*?:"<>|]', '', data['title'])
        filepath = downloader.download(data['url'], title)

        if filepath:
            return jsonify({
                'success': True,
                'path': filepath,
                'filename': os.path.basename(filepath)
            })
        return jsonify({'error': '下载失败'}), 500
    except Exception as e:
        return jsonify({'error': f'下载出错: {str(e)}'}), 500

@app.route('/batch', methods=['GET', 'POST'])
def batch_parse():
    if request.method == 'GET':
        return render_template('batch.html')

    urls = request.form.get('urls', '')
    url_list = [u.strip() for u in urls.split('\n') if u.strip()]

    if not url_list:
        return jsonify({'error': '请输入至少一个URL'}), 400

    results = []
    for url in url_list:
        try:
            platform = detect_platform(url)
            if platform and platform in PARSERS:
                parser = PARSERS[platform]
                result = parser.parse(url)
                result.update({
                    'platform': platform,
                    'original_url': url,
                    'status': 'success'
                })
            else:
                result = {
                    'original_url': url,
                    'status': 'failed',
                    'error': '不支持的平台'
                }
        except Exception as e:
            result = {
                'original_url': url,
                'status': 'failed',
                'error': str(e)
            }

        results.append(result)

    return render_template('batch_result.html', results=results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)