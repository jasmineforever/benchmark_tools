from typing import List, Dict, Optional, Union
import time


class RunResult:
    def __init__(self):
        self.worker_index = 0
        self.now_user = 0
        self.success_results: Union[None, List[float]] = None
        self.failed_reason: Union[None, Dict[str, int]] = None
        self.last_time: float = 0.0

        self.finish = False

    def __str__(self):
        return f'worker_index:{self.worker_index}\n' \
               f'now_user:{self.now_user}\n' \
               f'success_results len:{len(self.success_results)}\n' \
               f'last_time:{self.last_time}\n'


class FinalResult:
    def __init__(self, num_of_worker: int):
        self._users_list = [0] * num_of_worker
        self._users = 0
        self._failed_reasons = {}
        self._success_results = []
        self._last_time = 0
        self._run_time = 0

    @property
    def users(self) -> int:
        return self._users

    @property
    def failed_reasons(self) -> dict:
        return self._failed_reasons

    @property
    def success_results(self) -> List[float]:
        return self._success_results

    @property
    def run_time(self) -> float:
        return self._run_time

    @run_time.setter
    def run_time(self, value: float) -> None:
        self._run_time = value

    @property
    def last_time(self) -> float:
        return self._last_time

    def update(self, result: RunResult):
        self._users_list[result.worker_index] = result.now_user
        self._users = sum(self._users_list)
        self._success_results.extend(result.success_results)
        if result.last_time > self._last_time:
            self._last_time = result.last_time
        for failed_reason, count in result.failed_reason.items():
            if failed_reason in self._failed_reasons:
                self._failed_reasons[failed_reason] += count
            else:
                self._failed_reasons[failed_reason] = count


class BenchmarkContext:
    def __init__(self, worker_index: int):
        self._worker_index = worker_index
        self._users = 0
        self._failed_reason = {'_default': 0}
        self._success_results: List[float] = list()
        self._last_time = 0.0

    @property
    def success_results(self) -> List[float]:
        return self._success_results

    @property
    def users(self) -> int:
        return self._users

    @users.setter
    def users(self, value: int) -> None:
        self._users = value

    @property
    def current_result(self) -> RunResult:
        result = RunResult()
        result.worker_index = self._worker_index
        result.now_user = self._users
        result.failed_reason = self._failed_reason
        result.success_results = self._success_results
        result.last_time = time.time()
        return result

    def reset(self):
        self._failed_reason = {'_default': 0}
        self._success_results.clear()

    def report_success(self, time_second: float):
        self._success_results.append(time_second)

    def report_fail(self, fail_reason: Optional[str] = None) -> None:
        if fail_reason is None or len(fail_reason) == 0:
            self._failed_reason['_default'] += 1
            return
        if fail_reason not in self._failed_reason:
            self._failed_reason[fail_reason] = 0
        self._failed_reason[fail_reason] += 1


