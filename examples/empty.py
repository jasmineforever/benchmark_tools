import asyncio
from benchmark_tools import ClientProtocol
from typing import Union


class EmptyClient(ClientProtocol):
    def __init__(self):
        super().__init__()

    async def execute(self) -> Union[bool, None]:
        await asyncio.sleep(0.1)
