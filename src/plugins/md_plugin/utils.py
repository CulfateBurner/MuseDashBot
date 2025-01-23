import aiohttp

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 '
                  'Safari/537.36 Edg/130.0.0.0'
}

async def get_url_text(url):
    """获取URL的数据流"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=600) as resp:
            if resp.status == 200:
                return await resp.text()
            return None


async def get_url_bytes(url):
    """获取URL的字节流"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=600) as resp:
            if resp.status == 200:
                return await resp.read()
            return None
