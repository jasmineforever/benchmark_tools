import asyncio
from benchmark_tools import ClientProtocol
import aiohttp
from typing import Union, Optional


class HttpClient(ClientProtocol):
    json_str = None

    def __init__(self):
        super().__init__()
        self._url: Union[None, str] = None
        self._conn: Union[None, aiohttp.TCPConnector] = None
        self._session: Union[None, aiohttp.ClientSession] = None

    @staticmethod
    def global_init(custom_conf: Optional[dict] = None):
        assert custom_conf is not None
        with open(custom_conf['test_data_file'], 'r') as f:
            HttpClient.json_str = f.read()

    def init_before_use(self, host):
        self._conn = aiohttp.TCPConnector(limit=0)
        self._session = aiohttp.ClientSession(connector=self._conn, headers={'content-type': 'text/plain'})
        self._url = host

    async def shutdown(self) -> None:
        if self._session is not None:
            await self._session.close()

    async def execute(self) -> Optional[bool]:
        async with self._session.post(self._url, data=self.json_str) as response:
            # read all data
            _ = await response.text()
            if response.status != 200:
                raise ValueError(f'response with err http status code:{response.status}')
