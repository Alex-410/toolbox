from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import subprocess
import os
import sys
import re
import json
import threading
from queue import Queue, Empty

WORK_DIR = r'c:\Users\hp\Desktop\claude\anime-travel'

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def _decode(data):
    enc = sys.getdefaultencoding() or 'utf-8'
    for e in (enc, 'utf-8', 'gbk', 'latin-1'):
        try:
            return data.decode(e)
        except (UnicodeDecodeError, LookupError):
            pass
    return data.decode('utf-8', errors='replace')


def _clean(data):
    return _ANSI_RE.sub('', _decode(data))


def _reader(pipe, queue):
    try:
        for line in iter(pipe.readline, b''):
            queue.put(line)
    except (ValueError, OSError):
        pass
    finally:
        try:
            pipe.close()
        except Exception:
            pass


@csrf_exempt
def exec_command(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        body = json.loads(request.body)
        command = body.get('command', '').strip()
        cwd = body.get('cwd', WORK_DIR)
        wait_sec = min(int(body.get('timeout', 5)), 15)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not command:
        return JsonResponse({'error': 'Empty command'}, status=400)

    if not os.path.isdir(cwd):
        cwd = WORK_DIR

    try:
        proc = subprocess.Popen(
            command,
            cwd=cwd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stdout_q = Queue()
        stderr_q = Queue()

        t1 = threading.Thread(target=_reader, args=(proc.stdout, stdout_q), daemon=True)
        t2 = threading.Thread(target=_reader, args=(proc.stderr, stderr_q), daemon=True)
        t1.start()
        t2.start()

        try:
            proc.wait(timeout=wait_sec)
        except subprocess.TimeoutExpired:
            pass

        t1.join(timeout=1)
        t2.join(timeout=1)

        stdout_bytes = b''
        while not stdout_q.empty():
            try:
                stdout_bytes += stdout_q.get_nowait()
            except Empty:
                break

        stderr_bytes = b''
        while not stderr_q.empty():
            try:
                stderr_bytes += stderr_q.get_nowait()
            except Empty:
                break

        running = proc.poll() is None

        return JsonResponse({
            'stdout': _clean(stdout_bytes),
            'stderr': _clean(stderr_bytes),
            'returncode': proc.returncode if not running else None,
            'cwd': cwd,
            'running': running,
            'pid': proc.pid,
        })
    except Exception as e:
        return JsonResponse({
            'stdout': '',
            'stderr': str(e),
            'returncode': -1,
            'cwd': cwd,
            'running': False,
        })


urlpatterns = [
    path('exec/', exec_command, name='exec'),
]
