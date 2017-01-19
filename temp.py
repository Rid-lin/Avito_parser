# -*- coding: utf-8 -*-
import aiohttp
import asyncio


async def fetch(client):
    async with client.get('http://python.org', proxy="http://proxy.loc:8080") as resp:
        assert resp.status == 200
        return await resp.text()


async def main(loop):
    async with aiohttp.ClientSession(loop=loop) as client:
        html = await fetch(client)
        print(html)


loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
