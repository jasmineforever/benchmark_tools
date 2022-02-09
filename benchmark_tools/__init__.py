import os
import math
import copy
import time
from datetime import datetime
from typing import List, Union, Tuple
from multiprocessing import Process, Queue
import threading
import uvloop
from .helper import ThreadWrapper
from .benchmark_conf import BenchmarkConfig, load_benchmark_config_from_file
from .benchmark_tool import BenchmarkTool
from .benchmark_context import RunResult, FinalResult
from .client_protocol import ClientProtocol
from .benchmark_result import BenchmarkResult
from . import rps_dash


REPORT_INTERVAL = 1


def run_benchmark_in_process(index: int, conf: BenchmarkConfig):
    # print(f'using config in worker {index}, pid {os.getpid()}:{conf}')
    uvloop.install()
    tool = BenchmarkTool(index, conf, benchmark_tool.on_results, REPORT_INTERVAL)
    tool.run()


class BenchmarkTools:
    def __init__(self):
        self._rq = Queue()
        self._wq = Queue()
        self._processes: List[Process] = []
        self._config: [None, BenchmarkConfig] = None
        # don't copy data in worker process
        self._result: Union[None, FinalResult] = None
        self._calc_thread: Union[None, ThreadWrapper] = None
        self._lock: Union[None, threading.RLock] = None
        self._start_time: Union[None, float] = None
        self._mid_results: Union[None, List[RunResult]] = None
        self._realtime_rps: Union[None, List[Tuple[str, float]]] = None

    def run(self, config_file: str):
        config = load_benchmark_config_from_file(config_file)
        print('print using config:\n' + str(config))
        assert config.users >= config.worker
        workers_config = self.__generate_conf_for_workers(config)
        self._calc_thread = ThreadWrapper(target=self.__count_result)
        for i in range(config.worker):
            self._processes.append(Process(target=run_benchmark_in_process, args=(i, workers_config[i])))
        self._start_time = time.time()
        for process in self._processes:
            process.start()
        self._config = config
        self._mid_results = []
        self._realtime_rps = []
        self._result = FinalResult(config.worker)
        self._lock = threading.RLock()

        self._calc_thread.start()
        if self._config.enable_dash:
            rps_dash.run_dash_server(self._wq)

        wait_end_sigs = [False] * config.worker
        try:
            while True:
                result: RunResult = self._rq.get()
                # print(f'receive result in main process{result}')
                if result.finish:
                    wait_end_sigs[result.worker_index] = True
                with self._lock:
                    self._result.update(result)
                    if self._config.enable_dash and not result.finish:
                        self._update_realtime_result(result)
                if wait_end_sigs.count(True) == len(wait_end_sigs):
                    if self._config.enable_dash:
                        rps_dash.stop_dash_server()
                    self._calc_thread.shutdown()
                    # wait for sub process exit
                    time.sleep(3.0)
                    break
            print('final benchmark:')
            self._result.run_time = self._result.last_time - self._start_time
            fr = BenchmarkResult.generate_benchmark_result(self._result)
            fr.print()

            # import plotly.express as px
            # from pandas import DataFrame
            # df = DataFrame(self._realtime_rps, columns=['time', 'rps'])
            # fig = px.line(df, x='time', y='rps')
            # fig.update_yaxes(rangemode="tozero")
            # fig.update_layout(title=str(self._config))
            # fig.show()
        except KeyboardInterrupt:
            self._calc_thread.shutdown()

    def on_results(self, result: RunResult):
        self._rq.put_nowait(result)

    def __count_result(self, time_wait=5.0):
        while not self._calc_thread.need_quit():
            self.__print_current_result()
            time.sleep(time_wait)

    def _update_realtime_result(self, result: RunResult):
        count = 0
        self._mid_results.append(result)
        if len(self._mid_results) == self._config.worker:
            for r in self._mid_results:
                count += len(r.success_results)
            self._wq.put_nowait((datetime.now().strftime('%H:%M:%S'), count / float(REPORT_INTERVAL)))
            # self._realtime_rps.append((datetime.now().strftime('%H:%M:%S'), count / float(REPORT_INTERVAL)))
            self._mid_results.clear()

    def __print_current_result(self):
        with self._lock:
            self._result.run_time = self._result.last_time - self._start_time
            if self._result.run_time > 0.9:
                fr = BenchmarkResult.generate_benchmark_result(self._result)
                fr.print()

    @staticmethod
    def __generate_conf_for_workers(config: BenchmarkConfig) -> List[BenchmarkConfig]:
        # mod users and hatch rate
        base_count = math.floor(config.users / config.worker)
        add_user_count = config.users - base_count * config.worker
        hatch_rate = round(config.hatch_rate / config.worker)
        ret = []
        for i in range(config.worker):
            worker_config = copy.copy(config)
            if i < add_user_count:
                worker_config.users = base_count + 1
            else:
                worker_config.users = base_count
            worker_config.hatch_rate = hatch_rate
            ret.append(worker_config)
        return ret


benchmark_tool = BenchmarkTools()
