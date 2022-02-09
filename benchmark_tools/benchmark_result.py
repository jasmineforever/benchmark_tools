from benchmark_context import FinalResult
import math
from colorama import Fore, Back, Style


def get_prefix_format() -> str:
    return '{0:30}'


class BenchmarkResult:
    run_time_prefix = get_prefix_format().format('run time')
    users_prefix = get_prefix_format().format('users')
    fail_count_prefix = get_prefix_format().format('fail count')
    success_count_prefix = get_prefix_format().format('success count')
    rps_prefix = get_prefix_format().format('rps')
    accuracy_prefix = get_prefix_format().format('accuracy')
    avg_rep_time_prefix = get_prefix_format().format('average response time')
    min_rep_time_prefix = get_prefix_format().format('min response time')
    max_rep_time_prefix = get_prefix_format().format('max response time')
    rep_time_90_prefix = get_prefix_format().format('90% response time')
    rep_time_50_prefix = get_prefix_format().format('Median response time')

    def __init__(self):
        self._run_time: int = 0
        self._users: int = 0
        self._fail_count: int = 0
        self._success_count: int = 0
        self._rps: float = 0.0
        self._avg_rep_time: float = 0
        self._max_rep_time: float = 0
        self._min_rep_time: float = 0
        self._rep_time_90: float = 0
        self._rep_time_50: float = 0
        self._accuracy: float = 0.0
        self._failed_reasons = dict()

    @staticmethod
    def get_prefix_format() -> str:
        return '{0:25}'

    def __str__(self):
        return f'{self.run_time_prefix}:{self._run_time}\n'\
            f"{self.users_prefix}:{self._users}\n" \
            f"{self.success_count_prefix}:{self._success_count}\n" \
            f"{self.fail_count_prefix}:{self._fail_count}\n" \
            f"{self.rps_prefix}:{self._rps}\n" \
            f"{self.accuracy_prefix}:{self._accuracy}%\n" \
            f"{self.avg_rep_time_prefix}:{self._avg_rep_time} ms\n" \
            f"{self.min_rep_time_prefix}:{self._min_rep_time} ms\n" \
            f"{self.max_rep_time_prefix}:{self._max_rep_time} ms\n" \
            f"{self.rep_time_90_prefix}:{self._rep_time_90} ms\n" \
            f"{self.rep_time_50_prefix}:{self._rep_time_50} ms"

    def print(self):
        print(self.__str__())
        base = ''
        for reason, count in self._failed_reasons.items():
            if count > 0:
                base += f'count {count:6}: {reason}\n'
            if len(base) > 0:
                print(Fore.RED + f"failed reasons:\n" + base)
                print(Style.RESET_ALL)
        print('=' * 40)

    @staticmethod
    def __get_percent_index(array_len, percent: float):
        # percent(0.0 - 1.0)
        index = math.floor(array_len * percent) - 1
        if index < 0:
            index = 0
        return index

    @staticmethod
    def generate_benchmark_result(fr: FinalResult):
        r = BenchmarkResult()
        r._users = fr.users
        r._run_time = fr.run_time
        results = fr.success_results
        r._success_count = len(results)
        r._failed_reasons = fr.failed_reasons
        r._fail_count = sum([c for c in fr.failed_reasons.values()])
        r._rps = r._success_count / r._run_time
        if len(results) > 0:
            results.sort()
            r._avg_rep_time = int((sum(t for t in results) / len(results)) * 1000)
            r._min_rep_time = int((results[0]) * 1000)
            r._max_rep_time = int((results[-1]) * 1000)
            if len(results) > 9:
                r._rep_time_90 = int((results[BenchmarkResult.__get_percent_index(r._success_count, 0.9)]) * 1000)
                r._rep_time_50 = int((results[BenchmarkResult.__get_percent_index(r._success_count, 0.50)]) * 1000)
            r._accuracy = (r._success_count / (r._fail_count + r._success_count)) * 100
        return r
