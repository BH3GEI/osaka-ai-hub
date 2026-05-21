import time
import threading
import gc
import torch


class ModelSlot:
    def __init__(self, loader, unloader=None, ttl=600):
        self._loader = loader
        self._unloader = unloader
        self._ttl = ttl
        self._model = None
        self._last_used = 0
        self._lock = threading.Lock()

    def get(self):
        with self._lock:
            if self._model is None:
                self._model = self._loader()
            self._last_used = time.time()
            return self._model

    def try_evict(self):
        with self._lock:
            if self._model is None:
                return False
            if time.time() - self._last_used < self._ttl:
                return False
            if self._unloader:
                self._unloader(self._model)
            self._model = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            return True

    @property
    def loaded(self):
        return self._model is not None


class ModelManager:
    def __init__(self, evict_interval=60):
        self._slots: dict[str, ModelSlot] = {}
        self._timer = None
        self._evict_interval = evict_interval
        self._start_evictor()

    def register(self, name: str, loader, unloader=None, ttl=600):
        self._slots[name] = ModelSlot(loader, unloader, ttl)

    def get(self, name: str):
        if name not in self._slots:
            raise KeyError(f"Model '{name}' not registered")
        return self._slots[name].get()

    def status(self) -> dict:
        return {name: {"loaded": slot.loaded} for name, slot in self._slots.items()}

    def _evict_loop(self):
        for name, slot in self._slots.items():
            if slot.try_evict():
                print(f"[ModelManager] Evicted '{name}' (TTL expired)")
        self._timer = threading.Timer(self._evict_interval, self._evict_loop)
        self._timer.daemon = True
        self._timer.start()

    def _start_evictor(self):
        self._timer = threading.Timer(self._evict_interval, self._evict_loop)
        self._timer.daemon = True
        self._timer.start()
