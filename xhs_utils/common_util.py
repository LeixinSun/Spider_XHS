import json
import os
import time
from loguru import logger
from dotenv import load_dotenv

_DEBUG_ENABLED = False


def set_debug_enabled(enabled: bool):
    global _DEBUG_ENABLED
    _DEBUG_ENABLED = bool(enabled)


def is_debug_enabled():
    return _DEBUG_ENABLED


def load_env():
    load_dotenv()
    cookies_str = os.getenv('COOKIES')
    return cookies_str

def init():
    media_base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../datas/media_datas'))
    excel_base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../datas/excel_datas'))
    for base_path in [media_base_path, excel_base_path]:
        if not os.path.exists(base_path):
            os.makedirs(base_path)
            logger.info(f'创建目录 {base_path}')
    cookies_str = load_env()
    base_path = {
        'media': media_base_path,
        'excel': excel_base_path,
    }
    return cookies_str, base_path


def dump_debug_response(tag, payload):
    if not _DEBUG_ENABLED:
        return
    try:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../datas/debug_responses'))
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(base_path, f'{tag}_{timestamp}.json')
        with open(file_path, mode='w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=True)
        logger.info(f'保存调试响应 {file_path}')
    except Exception as e:
        logger.warning(f'保存调试响应失败: {e}')
