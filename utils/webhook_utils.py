import aiohttp

async def send_welcome_via_webhook(webhook_url, content=None, embed=None):
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(webhook_url, session=session)
        await webhook.send(content=content, embed=embed)

def is_valid_url(url):
    return url.startswith("http://") or url.startswith("https://")
