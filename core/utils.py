import re
import os
from datetime import datetime

def clean_filename(filename):
    """
    清理文件名中的非法字符
    :param filename: 原始文件名
    :return: 清理后的文件名
    """
    # 移除特殊字符
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    # 缩短过长文件名
    if len(filename) > 100:
        filename = filename[:50] + '...' + filename[-50:]
    return filename.strip()

def format_size(bytes_size):
    """
    格式化文件大小
    :param bytes_size: 字节大小
    :return: 格式化后的字符串
    """
    if bytes_size is None:
        return "未知大小"

    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def get_timestamp_filename(filename):
    """
    获取带时间戳的文件名
    :param filename: 原始文件名
    :return: 带时间戳的文件名
    """
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{name}_{timestamp}{ext}"