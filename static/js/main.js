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
            // 创建中止控制器
            const controller = new AbortController();
            window.downloadAbortController = controller; // 全局可访问

            // 显示进度条
            const progressBar = initProgressBar(title, type);

            const response = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                signal: controller.signal,
                body: JSON.stringify({
                    url: url,
                    title: title,
                    type: type
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || '下载失败');
            }

            /*const data = await response.json();

            if (response.ok) {
                // 直接触发下载
                // window.open(url, '_blank');

                // 或者使用更复杂的方法处理下载
                // const a = document.createElement('a');
                // a.href = url;
                // a.download = data.filename;
                // document.body.appendChild(a);
                // a.click();
                // document.body.removeChild(a);


            } else {
                showError(data.error || '下载失败');
            }*/

            // 获取文件名（从响应头或生成）
            const disposition = response.headers.get('Content-Disposition');
            const filename = disposition
                ? disposition.split('filename=')[1].replace(/"/g, '')
                : `${title}.${type}`;

            // 创建可读流
            const reader = response.body.getReader();
            const contentLength = +response.headers.get('Content-Length') || 0;
            let receivedLength = 0;
            const chunks = [];

            // 流式接收数据
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                chunks.push(value);
                receivedLength += value.length;

                // 更新进度
                progressBar.update(
                    contentLength > 0
                        ? Math.round((receivedLength / contentLength) * 100)
                        : null,
                    formatBytes(receivedLength),
                    contentLength > 0 ? formatBytes(contentLength) : '未知'
                );
            }

            // 创建下载链接
            const blob = new Blob(chunks);
            const blobUrl = URL.createObjectURL(blob);
            triggerDownload(blobUrl, filename);

            // 清理
            setTimeout(() => {
                URL.revokeObjectURL(blobUrl);
                progressBar.complete();
            }, 100);

        } catch (error) {
            if (error.name !== 'AbortError') {
            showError('下载请求失败');
            console.error('下载失败:', error);
            }
        }
    }

    // 辅助函数
    function initProgressBar(title, type) {
        const container = document.getElementById('download-progress');
        const bar = document.getElementById('progress-bar');
        const text = document.getElementById('progress-text');

        console.log(container)
        container.style.display = 'block';
        bar.style.width = '0%';
        text.textContent = `准备下载 ${title}.${type}...`;

        return {
            update: (percent, loaded, total) => {
                bar.style.width = `${percent || 0}%`;
                text.textContent = percent
                    ? `${title}.${type} - ${percent}% (${loaded}/${total})`
                    : `${title}.${type} - 已下载 ${loaded}`;
            },
            complete: () => {
                text.textContent = '下载完成！';
                setTimeout(() => {
                    container.style.display = 'none';
                }, 2000);
            }
        };
    }

    function triggerDownload(url, filename) {
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    function formatBytes(bytes) {
        if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(2) + ' GB';
        if (bytes >= 1048576) return (bytes / 1048576).toFixed(2) + ' MB';
        if (bytes >= 1024) return (bytes / 1024).toFixed(2) + ' KB';
        return bytes + ' bytes';
    }

// 取消下载函数
    function cancelDownload() {
        if (window.downloadAbortController) {
            window.downloadAbortController.abort();
            showMessage('下载已取消');
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