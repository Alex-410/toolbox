import subprocess
import os
import time
import logging
import re

logger = logging.getLogger(__name__)

ANIME_TRAVEL_DIR = r'c:\Users\hp\Desktop\claude\anime-travel'
_anime_travel_url = None


def get_anime_travel_url():
    return _anime_travel_url


def start_anime_travel_service():
    global _anime_travel_url

    if _anime_travel_url:
        logger.info(f"Already started at {_anime_travel_url}")
        return {'success': True, 'url': _anime_travel_url}

    logger.info("Starting anime travel service...")

    try:
        env = os.environ.copy()
        env['NO_PROXY'] = 'localhost,127.0.0.1'

        process = subprocess.Popen(
            'npm run dev',
            cwd=ANIME_TRAVEL_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            bufsize=1,
        )

        logger.info(f"Process started with PID: {process.pid}")

        start_time = time.time()
        timeout = 20

        while time.time() - start_time < timeout:
            raw = process.stdout.readline()
            if not raw:
                if process.poll() is not None:
                    break
                continue

            line = raw.decode('utf-8', errors='replace').strip()
            if line:
                logger.info(f"[npm] {line}")

            match = re.search(r'Local:\s+(http://[^\s]+)', line)
            if match:
                _anime_travel_url = match.group(1).rstrip('/')
                logger.info(f"Detected URL: {_anime_travel_url}")
                return {'success': True, 'url': _anime_travel_url}

        logger.warning("Could not detect URL from npm output")
        return {'success': False, 'error': '无法获取启动地址，npm 未输出 Local URL'}

    except Exception as e:
        logger.error(f"Failed to start anime travel service: {e}")
        return {'success': False, 'error': str(e)}
