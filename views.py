import asyncio
import contextlib
import logging
import sys
from os import name, system
from re import compile, search
from time import sleep

import aiohttp
from aiohttp_socks import ProxyConnector
from telethon import Button, TelegramClient, events

from config import *

logging.basicConfig(level=logging.WARNING)
LOGS = logging.getLogger()
client = TelegramClient("LegendBoy", API_ID, API_HASH).start(bot_token=TOKEN)


# ============== Function ====================
def check_sudo(user_id):
    if user_id in SUDO_USERS:
        return True
    return False


# =================== Button =================
owner_keyboard = [[Button.url("Owner", url="https://t.me/LegendBoy_OP")]]


# ===================== Command =================
@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    if not check_sudo(event.sender_id):
        return await event.reply(
            "Hello Sir,\n\nWelcome To Telegram views script bot which help to increase view on post automatically.To Buy this bot contact my boss.\n\n        Thanks 🙏.",
            buttons=owner_keyboard,
        )
    await event.reply(
        "Hello Sir,\n\nWelcome To Telegram views script bot which help to increase view on post automatically.To Buy this bot contact my boss.\n\n        Thanks 🙏.",
        buttons=owner_keyboard,
    )


user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
REGEX = compile(
    r"(?:^|\D)?(("
    + r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
    + r"\."
    + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
    + r"\."
    + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
    + r"\."
    + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
    + r"):"
    + (
        r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
        + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])"
    )
    + r")(?:\D|$)"
)


class Telegram:
    def __init__(self, channel: str, post: int) -> None:
        # Async Tasks
        self.tasks = 225

        self.channel = channel
        self.post = post

        self.cookie_error = 0
        self.sucsess_sent = 0
        self.failled_sent = 0
        self.token_error = 0
        self.proxy_error = 0

    async def request(self, proxy: str, proxy_type: str):
        if proxy_type == "socks4":
            connector = ProxyConnector.from_url(f"socks4://{proxy}")
        elif proxy_type == "socks5":
            connector = ProxyConnector.from_url(f"socks5://{proxy}")
        elif proxy_type == "https":
            connector = ProxyConnector.from_url(f"https://{proxy}")
        else:
            connector = ProxyConnector.from_url(f"http://{proxy}")

        jar = aiohttp.CookieJar(unsafe=True)
        async with aiohttp.ClientSession(
            cookie_jar=jar, connector=connector
        ) as session:
            try:
                async with session.get(
                    f"https://t.me/{self.channel}/{self.post}?embed=1&mode=tme",
                    headers={
                        "referer": f"https://t.me/{self.channel}/{self.post}",
                        "user-agent": user_agent,
                    },
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as embed_response:
                    if jar.filter_cookies(embed_response.url).get("stel_ssid"):
                        views_token = search(
                            'data-view="([^"]+)"', await embed_response.text()
                        )
                        if views_token:
                            views_response = await session.post(
                                "https://t.me/v/?views=" + views_token.group(1),
                                headers={
                                    "referer": f"https://t.me/{self.channel}/{self.post}?embed=1&mode=tme",
                                    "user-agent": user_agent,
                                    "x-requested-with": "XMLHttpRequest",
                                },
                                timeout=aiohttp.ClientTimeout(total=5),
                            )
                            if (
                                await views_response.text() == "true"
                                and views_response.status == 200
                            ):
                                self.sucsess_sent += 1
                            else:
                                self.failled_sent += 1
                        else:
                            self.token_error += 1
                    else:
                        self.cookie_error += 1
            except:
                self.proxy_error += 1
            finally:
                jar.clear()

    def run_proxies_tasks(self, lines: list, proxy_type):
        async def inner(proxies: list):
            await asyncio.wait(
                [
                    asyncio.create_task(self.request(proxy, proxy_type))
                    for proxy in proxies
                ]
            )

        chunks = [lines[i : i + self.tasks] for i in range(0, len(lines), self.tasks)]
        for chunk in chunks:
            asyncio.run(inner(chunk))

    def run_auto_tasks(self):
        while True:

            async def inner(proxies: tuple):
                await asyncio.wait(
                    [
                        asyncio.create_task(self.request(proxy, proxy_type))
                        for proxy_type, proxy in proxies
                    ]
                )

            auto = Auto()
            chunks = [
                auto.proxies[i : i + self.tasks]
                for i in range(0, len(auto.proxies), self.tasks)
            ]
            for chunk in chunks:
                asyncio.run(inner(chunk))

    async def run_rotated_task(self, proxy, proxy_type):
        while True:
            await asyncio.wait(
                [
                    asyncio.create_task(self.request(proxy, proxy_type))
                    for _ in range(self.tasks)
                ]
            )

    def cli(self):
        logo = """
        ~ Telegram Auto Views V4 ~
          ~ github.com/TeaByte ~
               ~ @TeaByte ~
        """
        while not self.sucsess_sent:
            print(logo)
            print("\n\n        [ Waiting... ]\r")
            sleep(0.3)
            system("cls" if name == "nt" else "clear")

        while True:
            print(logo)
            print(
                f"""
        DATA: 
        @{self.channel}/{self.post}
        Sent: {self.sucsess_sent}
        Fail: {self.failled_sent}

        ERRORS:
        Proxy Error:  {self.proxy_error}
        Token Error:  {self.token_error}
        Cookie Error: {self.cookie_error}
            """
            )
            sleep(0.3)
            system("cls" if name == "nt" else "clear")


class Auto:
    def __init__(self):
        self.proxies = []
        try:
            with open(f"auto/http.txt", "r") as file:
                self.http_sources = file.read().splitlines()

            with open(f"auto/socks4.txt", "r") as file:
                self.socks4_sources = file.read().splitlines()

            with open(f"auto/http.txt", "r") as file:
                self.socks5_sources = file.read().splitlines()

        except FileNotFoundError:
            print(" [ Error ] auto file not found!")
            exit()

        print(" [ WAIT ] Scraping proxies... ")
        asyncio.run(self.init())

    async def scrap(self, source_url, proxy_type):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    source_url,
                    headers={"user-agent": user_agent},
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:
                    html = await response.text()
                    if tuple(REGEX.finditer(html)):
                        for proxy in tuple(REGEX.finditer(html)):
                            self.proxies.append((proxy_type, proxy.group(1)))
        except Exception as e:
            with open("error.txt", "a", encoding="utf-8", errors="ignore") as f:
                f.write(f"{source_url} -> {e}\n")

    async def init(self):
        tasks = []
        self.proxies.clear()
        for sources in (
            (self.http_sources, "http"),
            (self.socks4_sources, "socks4"),
            (self.socks5_sources, "socks5"),
        ):
            srcs, proxy_type = sources
            for source_url in srcs:
                task = asyncio.create_task(self.scrap(source_url, proxy_type))
                tasks.append(task)
        await asyncio.wait(tasks)


@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def tg_views(event):
    print(event)


if len(sys.argv) in {1, 3, 4}:
    with contextlib.suppress(ConnectionError):
        client.run_until_disconnected()
else:
    client.disconnect()
