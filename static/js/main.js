document.addEventListener('DOMContentLoaded', function() {
    const parseBtn = document.getElementById('parseBtn');
    const videoUrl = document.getElementById('videoUrl');
    const resultArea = document.getElementById('resultArea');

    parseBtn.addEventListener('click', parseVideo);

    // 回车键触发解析
    videoUrl.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            parseVideo();
        }
    });

    async function parseVideo() {
        const url = videoUrl.value.trim();
        if (!url) {
            showError('请输入视频链接');
            return;
        }

        parseBtn.disabled = true;
        parseBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 解析中...';

        try {
            const response = await fetch('/parse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `url=${encodeURIComponent(url)}`
            });

            const data = await response.json();

            if (data.error) {
                showError(data.error);
            } else {
                showResult(data);
            }
        } catch (error) {
            showError('网络错误，请重试');
            console.error('解析失败:', error);
        } finally {
            parseBtn.disabled = false;
            parseBtn.innerHTML = '<i class="bi bi-magic"></i> 解析视频';
        }
    }

    function showResult(data) {
        const template = document.getElementById('resultTemplate').content.cloneNode(true);

        // 填充基本信息
        template.getElementById('resultTitle').textContent = data.title || '无标题';
        template.getElementById('resultPlatform').textContent = getPlatformName(data.platform);
        template.getElementById('resultAuthor').textContent = data.author || '未知作者';
        template.getElementById('originalLink').href = data.original_url;

        // 设置封面
        const coverImg = template.getElementById('resultCover');
        if (data.cover) {
            coverImg.src = data.cover;
            coverImg.alt = data.title || '视频封面';
        } else {
            coverImg.src = 'https://via.placeholder.com/300x200?text=No+Cover';
        }

        // 设置时长
        const durationBadge = template.getElementById('resultDuration');
        if (data.duration) {
            durationBadge.textContent = formatDuration(data.duration);
            durationBadge.style.display = 'inline-block';
        } else {
            durationBadge.style.display = 'none';
        }

        // 添加下载选项
        const downloadOptions = template.getElementById('downloadOptions');
        if (data.downloads && data.downloads.length > 0) {
            data.downloads.forEach(option => {
                const optionTemplate = document.getElementById('downloadOptionTemplate').content.cloneNode(true);
                optionTemplate.querySelector('#optionQuality').textContent = option.quality;
                optionTemplate.querySelector('#optionType').textContent = option.type.toUpperCase();

                if (option.size) {
                    optionTemplate.querySelector('#optionSize').textContent = `${option.size}MB`;
                } else {
                    optionTemplate.querySelector('#optionSize').textContent = '';
                }

                const downloadBtn = optionTemplate.querySelector('.btn');
                downloadBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    downloadVideo(option.url, data.title, option.type);
                });

                downloadOptions.appendChild(optionTemplate);
            });
        } else {
            downloadOptions.innerHTML = '<div class="alert alert-warning">没有可用的下载选项</div>';
        }

        resultArea.innerHTML = '';
        resultArea.appendChild(template);
    }

    function showError(message) {
        const template = document.getElementById('errorTemplate').content.cloneNode(true);
        template.getElementById('errorMessage').textContent = message;
        resultArea.innerHTML = '';
        resultArea.appendChild(template);
    }

    async function downloadVideo(url, title, type) {
        try {
            const response = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url,
                    title: title,
                    type: type
                })
            });

            const data = await response.json();

            if (data.success) {
                // 直接触发下载
                window.open(url, '_blank');

                // 或者使用更复杂的方法处理下载
                // const a = document.createElement('a');
                // a.href = url;
                // a.download = data.filename;
                // document.body.appendChild(a);
                // a.click();
                // document.body.removeChild(a);
            } else {
                showError(data.error || '下载失败');
            }
        } catch (error) {
            showError('下载请求失败');
            console.error('下载失败:', error);
        }
    }

    function getPlatformName(platform) {
        const platforms = {
            'douyin': '抖音',
            'kuaishou': '快手',
            'bilibili': '哔哩哔哩',
            'youtube': 'YouTube'
        };
        return platforms[platform] || platform;
    }

    function formatDuration(seconds) {
        if (!seconds) return '';
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
});