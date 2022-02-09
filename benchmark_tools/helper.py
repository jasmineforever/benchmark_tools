import importlib.util
from client_protocol import ClientProtocol
import threading


class ThreadWrapper(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._close_ev = threading.Event()

    def shutdown(self):
        self._close_ev.set()
        self.join()

    def need_quit(self):
        return self._close_ev.isSet()


def load_benchmark_class_from_file(file_path: str) -> type:
    spec = importlib.util.spec_from_file_location("benchmark_tools", file_path)
    mo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mo)
    for k, v in mo.__dict__.items():
        if isinstance(v, type) and issubclass(v, ClientProtocol) and k != 'ClientProtocol':
            return v
    raise ValueError('load benchmark class failed')
