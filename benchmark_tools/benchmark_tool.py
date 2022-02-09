import asyncio
import logging
import time
import random
import cmath
from copy import deepcopy
from typing import List, Callable, Union, Tuple
from client_protocol import ClientProtocol
from benchmark_conf import BenchmarkConfig
from benchmark_context import BenchmarkContext
from helper import load_benchmark_class_from_file
from benchmark_context import RunResult


class BenchmarkTool:
    def __init__(self,
                 index: int,
                 conf: BenchmarkConfig,
                 result_callback: Callable[[RunResult], None],
                 callback_interval: int = 1):
        assert callback_interval >= 1
        my_class = load_benchmark_class_from_file(conf.benchmark_class_file)
        if my_class is None:
            raise ValueError(f'can not load benchmark client from:{conf.benchmark_class_file}')
        self._ClientClass = my_class
        self._config = conf
        self._clients: List[Union[ClientProtocol, None]] = [None] * self._config.users
        self._is_time_done = False
        self._benchmark_context = BenchmarkContext(index)

        self._on_result = result_callback
        self._call_interval = callback_interval
        if cmath.isclose(conf.wait_time[0], 0.0) and cmath.isclose(conf.wait_time[0], 0.0):
            self._need_wait = False
        else:
            self._need_wait = True

    def run(self) -> None:
        self._ClientClass.global_init(self._config.custom_config)  # type: ignore[arg-type]
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(asyncio.gather(self.__time_loop(), self.__executes()))
        except KeyboardInterrupt:
            pass

    async def __time_loop(self) -> None:
        count = 0
        users_count = 0
        for i in range(self._config.run_time):
            # 每秒自增长客户端
            users_count = sum(1 for client in self._clients if client is not None)
            if users_count < self._config.users:
                loop_count = min(self._config.users - users_count, self._config.hatch_rate)
                for j in range(users_count, users_count + loop_count):
                    self._clients[j] = self._ClientClass()
                    self._clients[j].set_context(self._benchmark_context)
                    self._clients[j].init_before_use(self._config.host)
            await asyncio.sleep(1.0)
            # 统计结果
            count += 1
            if count >= self._call_interval:
                self._benchmark_context.users = sum(1 for client in self._clients if client is not None)
                result = deepcopy(self._benchmark_context.current_result)
                self._on_result(result)
                self._benchmark_context.reset()

        self._is_time_done = True
        self._benchmark_context.users = users_count
        result = deepcopy(self._benchmark_context.current_result)
        result.finish = True
        self._on_result(result)

    async def __wait_for_next_call(self):
        if self._need_wait:
            await asyncio.sleep(self.__get_wait_time(self._config.wait_time))

    @staticmethod
    def __get_wait_time(wait_time: Tuple[float, float]) -> float:
        min_wait, max_wait = wait_time
        return min_wait if cmath.isclose(min_wait, max_wait) \
            else random.uniform(min_wait, max_wait)

    async def __executes(self):
        tasks = [self.__execute(i) for i in range(len(self._clients))]
        await asyncio.gather(*tasks)

    async def __execute(self, client_index):
        while not self._is_time_done:
            if self._clients[client_index] is not None:
                try:
                    st = time.time()
                    ret = await self._clients[client_index].execute()
                except Exception as e:
                    self._clients[client_index].report_fail(f'exception: type {type(e)}, msg:{str(e)}')
                else:
                    if ret:
                        pass
                    else:
                        self._clients[client_index].report_success(time.time() - st)
                await self.__wait_for_next_call()
            else:
                await asyncio.sleep(0.1)
        for client in self._clients:
            if client is not None:
                try:
                    await asyncio.wait_for(client.shutdown(), timeout=5.0)
                except asyncio.TimeoutError:
                    logging.warning(f'timeout in shutdown client, maybe you can fix it')
