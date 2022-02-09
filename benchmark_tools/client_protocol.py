from abc import ABCMeta, abstractmethod
from typing import Optional, Mapping, Any, Union
from .benchmark_context import BenchmarkContext


class ClientProtocol(metaclass=ABCMeta):
    def __init__(self):
        self._context: Union[None, BenchmarkContext] = None

    def set_context(self, context: BenchmarkContext):
        self._context = context

    @staticmethod
    def global_init(custom_conf: Optional[dict] = None) -> None:
        """
        init global resource, such as load your test cases from file

        :return: None
        """
        pass

    @staticmethod
    def update_custom_report(run_time: float) -> Optional[Mapping[str, Any]]:
        """
        This function is used to count custom data, and the returned key-value will be printed

        :param run_time: Time interval since the last statistics

        :return: custom data mapping
        """
        pass

    def init_before_use(self, host: str) -> None:
        """
        this func will be called once at the time that init per client

        :param host: your server address

        :return: None
        """
        pass

    @abstractmethod
    async def execute(self) -> Optional[bool]:
        """
        execute your request, and you need to report result in this func

        :return: None
        """
        raise NotImplementedError()

    async def shutdown(self) -> None:
        pass

    def report_success(self, time_second: float):
        self._context.report_success(time_second)

    def report_fail(self, fail_reason: str = ''):
        self._context.report_fail(fail_reason)

