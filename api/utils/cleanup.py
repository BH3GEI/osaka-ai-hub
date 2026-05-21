import os
import time
import threading
from pathlib import Path


OUR_PREFIXES = ("musetalk_",)


def cleanup_old_files(directory: Path, max_age_seconds=3600):
    if not directory.exists():
        return 0
    count = 0
    now = time.time()
    is_tmp = str(directory) == "/tmp"
    for item in directory.iterdir():
        if is_tmp and not any(item.name.startswith(p) for p in OUR_PREFIXES):
            continue
        try:
            age = now - item.stat().st_mtime
        except OSError:
            continue
        if age < max_age_seconds:
            continue
        if item.is_file():
            item.unlink()
            count += 1
        elif item.is_dir():
            import shutil
            shutil.rmtree(item, ignore_errors=True)
            count += 1
    return count


class AutoCleaner:
    def __init__(self, directories: list[Path], interval=600, max_age=3600):
        self._dirs = directories
        self._interval = interval
        self._max_age = max_age
        self._timer = None
        self._start()

    def _run(self):
        for d in self._dirs:
            cleaned = cleanup_old_files(d, self._max_age)
            if cleaned:
                print(f"[AutoCleaner] Cleaned {cleaned} items from {d}")
        self._timer = threading.Timer(self._interval, self._run)
        self._timer.daemon = True
        self._timer.start()

    def _start(self):
        self._timer = threading.Timer(self._interval, self._run)
        self._timer.daemon = True
        self._timer.start()
