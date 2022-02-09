import os.path
import yaml
import re
from typing import Tuple, Union, Optional

from yaml.constructor import Constructor


def add_bool(self, node):
    return self.construct_scalar(node)


Constructor.add_constructor(u'tag:yaml.org,2002:bool', add_bool)


class BenchmarkConfig:
    def __init__(self, config_obj: dict):
        self._host = config_obj['host']
        self._users = config_obj['users']
        self._hatch_rate = config_obj['hatch_rate']
        self._run_time = config_obj['run_time']
        self._min_wait_time = config_obj['min_wait_time']
        self._max_wait_time = config_obj['max_wait_time']
        self._worker = config_obj['worker']
        self._benchmark_class_file = config_obj['benchmark_class_file']
        self._enable_dash = config_obj['enable_dash']
        self._custom_config: Union[None, dict] = config_obj['custom_config']

    def __str__(self):
        return f'host: {self._host}\n' \
               f'users: {self._users}\n' \
               f'hatch_rate: {self._hatch_rate}\n' \
               f'run_time: {self.run_time}\n' \
               f'wait_time: {self._min_wait_time} - {self._max_wait_time}\n' \
               f'worker: {self._worker}\n' \
               f'benchmark_class_file: {self._benchmark_class_file}\n' \
               f'enable_dash: {self._enable_dash}\n' \
               f'custom_config: {self._custom_config}'

    @property
    def host(self) -> str:
        return self._host

    @property
    def users(self) -> int:
        return self._users

    @users.setter
    def users(self, value: int) -> None:
        assert value > 0
        self._users = value

    @property
    def hatch_rate(self) -> int:
        return self._hatch_rate

    @hatch_rate.setter
    def hatch_rate(self, value: int) -> None:
        assert value > 0
        self._hatch_rate = value

    @property
    def run_time(self) -> int:
        return self._run_time

    @property
    def wait_time(self) -> Tuple[float, float]:
        return self._min_wait_time, self._max_wait_time

    @property
    def benchmark_class_file(self) -> str:
        return self._benchmark_class_file

    @property
    def worker(self) -> int:
        return self._worker

    @property
    def enable_dash(self) -> bool:
        return self._enable_dash

    @property
    def custom_config(self) -> Optional[dict]:
        return self._custom_config


def load_benchmark_config_from_file(conf_file: str) -> BenchmarkConfig:
    with open(conf_file, 'r') as f:
        c = yaml.safe_load(f.read())
        if 'host' in c and isinstance(c['host'], str) and len(c['host']) > 0:
            pass
        else:
            raise ValueError('config err: "host" must be set with string type')
        if 'users' in c and isinstance(c['users'], int) and c['users'] > 0:
            pass
        else:
            raise ValueError('config err: "users" need >=0')
        if 'hatch_rate' in c:
            if isinstance(c['hatch_rate'], int) and c['hatch_rate'] >= 0:

                if c['hatch_rate'] == 0 or c['hatch_rate'] > c['users']:
                    c['hatch_rate'] = c['users']
            else:
                raise ValueError('config err: "hatch_rate" need >= 0')
        else:
            c['hatch_rate'] = c['users']

        if 'run_time' in c:
            if isinstance(c['run_time'], int) and c['run_time'] > 0:
                pass
            else:
                raise ValueError('config err: "run_time" need >= 1')
        else:
            c['run_time'] = 24 * 3600
        if 'wait_time' in c:
            wt = c['wait_time']
            if type(wt) is int:
                if wt == 0:
                    c['min_wait_time'] = 0.0
                    c['max_wait_time'] = 0.0
                elif wt > 0:
                    c['min_wait_time'] = float(wt)
                    c['max_wait_time'] = float(wt)
                else:
                    raise ValueError('config err:"wait_time" format err')
            elif type(wt) is float:
                if wt < 0.001:
                    c['min_wait_time'] = 0.0
                    c['max_wait_time'] = 0.0
                else:
                    c['min_wait_time'] = float(wt)
                    c['max_wait_time'] = float(wt)

            elif type(wt) is str:
                match_pattern = r'\s*[-~]\s*'
                wta = re.split(match_pattern, wt)
                if len(wta) == 1:
                    try:
                        wait_time = float(wta[0])
                        if wait_time < 0.001:
                            c['min_wait_time'] = 0.0
                            c['max_wait_time'] = 0.0
                        else:
                            c['min_wait_time'] = wait_time
                            c['max_wait_time'] = wait_time
                    except Exception as e:
                        raise ValueError('config err:"wait_time" format err') from e

                elif len(wta) == 2:
                    try:
                        min_wait_time = float(wta[0].strip(' \t'))
                        max_wait_time = float(wta[1].strip(' \t'))
                        if min_wait_time < max_wait_time:
                            if min_wait_time < 0.001:
                                c['min_wait_time'] = 0.0
                            else:
                                c['min_wait_time'] = min_wait_time
                            if max_wait_time < 0.001:
                                c['max_wait_time'] = 0.0
                            else:
                                c['max_wait_time'] = max_wait_time
                        else:
                            if min_wait_time < 0.001:
                                c['min_wait_time'] = 0.0
                                c['max_wait_time'] = 0.0
                            else:
                                c['min_wait_time'] = min_wait_time
                                c['max_wait_time'] = min_wait_time
                    except Exception as e:
                        raise ValueError('config err:"wait_time" format err') from e
                else:
                    raise ValueError('config err:"wait_time" format err')
            else:
                raise ValueError('config err:"wait_time" format err')
        else:
            c['min_wait_time'] = 0.0
            c['max_wait_time'] = 0.0

        if 'worker' in c:
            if isinstance(c['worker'], int) and c['worker'] >= 1:
                pass
            else:
                raise ValueError('config err: "worker" need >= 1')
        else:
            c['worker'] = 1

        if 'benchmark_class_file' in c and isinstance('benchmark_class_file', str) \
                and os.path.isfile(c['benchmark_class_file']):
            pass
        else:
            raise ValueError('config err: "benchmark_class_file" not set or found')

        if 'enable_dash' in c:
            if type(c['enable_dash']) == bool:
                pass
            else:
                raise ValueError('config err: "enable_dash" must be boolean type')
        else:
            c['enable_dash'] = False

        custom_config = {}
        for k, v in c.items():
            if k not in ['host', 'users', 'hatch_rate', 'run_time',
                         'worker', 'benchmark_class_file', 'wait_time',
                         'min_wait_time', 'max_wait_time', 'enable_dash']:
                custom_config[k] = v

        c['custom_config'] = custom_config if len(custom_config) > 0 else None
        return BenchmarkConfig(c)
