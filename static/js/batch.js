document.addEventListener('DOMContentLoaded', function() {
    const batchParseBtn = document.getElementById('batchParseBtn');
    const batchUrls = document.getElementById('batchUrls');
    const batchResultArea = document.getElementById('batchResultArea');

    batchParseBtn.addEventListener('click', parseBatchVideos);

    async function parseBatchVideos() {
        const urls = batchUrls.value.trim();
        if (!urls) {
            alert('请输入至少一个视频链接');
            return;
        }

        const urlList = urls.split('\n').filter(url => url.trim());
        if (urlList.length === 0) {
            alert('请输入有效的视频链接');
            return;
        }

        batchParseBtn.disabled = true;
        batchParseBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 解析中...';

        try {
            const response = await fetch('/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `urls=${encodeURIComponent(urls)}`
            });

            if (response.redirected) {
                window.location.href = response.url;
                return;
            }

            const data = await response.json();
            if (data.error) {
                showBatchError(data.error);
            } else {
                showBatchResults(data.results);
            }
        } catch (error) {
            showBatchError('批量解析失败: ' + error.message);
            console.error('批量解析失败:', error);
        } finally {
            batchParseBtn.disabled = false;
            batchParseBtn.innerHTML = '<i class="bi bi-magic"></i> 开始解析';
        }
    }

    function showBatchResults(results) {
        batchResultArea.innerHTML = '';

        if (!results || results.length === 0) {
            batchResultArea.innerHTML = `
            <div class="alert alert-warning">
                没有获取到任何解析结果
            </div>
            `;
            return;
        }

        const successCount = results.filter(r => r.status === 'success').length;
        const errorCount = results.length - successCount;

        // 添加统计信息
        batchResultArea.innerHTML += `
        <div class="card shadow-sm mb-4">
            <div class="card-header bg-light">
                <div class="d-flex justify-content-between align-items-center">
                    <span>解析统计</span>
                    <span class="badge bg-primary">
                        成功: ${successCount} / 失败: ${errorCount}
                    </span>
                </div>
            </div>
            <div class="card-body">
                <div class="progress mb-2">
                    <div class="progress-bar bg-success" role="progressbar" 
                         style="width: ${(successCount / results.length) * 100}%" 
                         aria-valuenow="${(successCount / results.length) * 100}" 
                         aria-valuemin="0" 
                         aria-valuemax="100"></div>
                </div>
                <div class="d-flex justify-content-between small text-muted">
                    <span>成功率: ${Math.round((successCount / results.length) * 100)}%</span>
                    <span>总计: ${results.length}个链接</span>
                </div>
            </div>
        </div>
        `;

        // 添加每个结果
        results.forEach((result, index) => {
            if (result.status === 'success') {
                showBatchSuccessItem(result, index + 1);
            } else {
                showBatchErrorItem(result, index + 1);
            }
        });
    }