# Скрипт получает необходимое кол-во MTProxy из телеграм канала https://t.me/mtp4tg
# Проверяет подключение и формирует 2 файла - рабочие и нерабочие прокси



# -- -- -- Получаем данные из .env -- -- -- #
import os
from dotenv import load_dotenv
load_dotenv()

# Данные от телеграм аккаунта
    # Используется для получания всех постов из телеграм канала
API_ID = API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')

# Данные от российского прокси
    # Используется для проверки доступности MTProxy из России
RUPROXY_USER = os.getenv('RUPROXY_USER')
RUPROXY_PASS = os.getenv('RUPROXY_PASS')
RUPROXY_HOST = 'dc01.steelproxy.com'
RUPROXY_PORT = 3072

# Названия файлов для MTProxy
FILE_WORKING_MTPROXY = 'working_mtproxy.txt'
FILE_DEAD_MTPROXY = 'dead_mtproxy.txt'

# Телеграм канал и необходимое кол-во MTProxy
TG_CHANNEL = 'mtp4tg'
TG_AMOUNT = 100



# -- -- -- Необходимые библиотеки -- -- -- #
from telethon import TelegramClient

import asyncio
import time
import json

import socket
import socks

from dataclasses import dataclass
from urllib.request import Request, urlopen



# -- -- -- Контейнер для MTProxy -- -- -- #
@dataclass
class ProxyItem:
    server: str
    port: int
    secret: str
    source_id: int | None = None



# -- -- -- Вытаскиваем данные MTProxy из сообщения -- -- -- #
def parse_message(text: str) -> ProxyItem | None:
    server = None
    port = None
    secret = None

    # Поиск нужных строк
    for line in text.replace('\r', '').split('\n'):
        line = line.strip().strip('*`')

        if line.startswith('Server:'):
            server = line.split(':', 1)[1].strip()

        elif line.startswith('Port:'):
            port = int(line.split(':', 1)[1].strip())

        elif line.startswith('Secret:'):
            secret = line.split(':', 1)[1].strip()

    # Если что-то не найдено, возвращаем None
    if not server or not port or not secret:
        return None

    return ProxyItem(server = server, port = port, secret = secret)



# -- -- -- Получаем канал, необходимое кол-во сообщений, обрабатываем в parse_message() и возвращаем список проскси -- -- -- #
async def fetch_proxies() -> list[ProxyItem]:
    client = TelegramClient('session', API_ID, API_HASH)
    proxies = []
    
    async with client:
        entity = await client.get_entity(TG_CHANNEL)
        
        async for msg in client.iter_messages(entity, limit = TG_AMOUNT):
            raw = msg.raw_text or ''
            item = parse_message(raw)

            if item:
                item.source_id = msg.id 
                proxies.append(item)

        return proxies



# -- -- -- Получаем флаг страны MTProxy -- -- -- #
def get_flag(host: str):
    try:
        ip = socket.gethostbyname(host)
        url = f'http://ip-api.com/json/{ip}?fields=status,countryCode'
        req = Request(url, headers = {'User-Agent': 'Mozilla/5.0'})

        with urlopen(req, timeout = 1) as resp:
            data = json.load(resp)
            code = data.get('countryCode', '🏳')

            if len(code) != 2:
                return '🏳'
            return chr(ord(code[0].upper()) + 127397) + chr(ord(code[1].upper()) + 127397)

    except:
        return '🏳'



# -- -- -- Проверяем подключение к MTProxy -- -- --
def check_connection(item: ProxyItem):
    start = time.perf_counter()

    try:
        sock = None
        sock = socks.socksocket()
        sock.set_proxy(
            proxy_type = socks.SOCKS5,
            addr = RUPROXY_HOST,
            port = RUPROXY_PORT,
            username = RUPROXY_USER,
            password = RUPROXY_PASS,
        )
        sock.settimeout(3)

        sock.connect((item.server, item.port))
        ms = int(round((time.perf_counter() - start) * 1000, 0))
        return True, ms

    except:
        return False, 0

    finally:
        if sock is not None:
            sock.close()



# -- -- -- Форматирование рабочих и нерабочих прокси -- -- -- #
def format_working(item: ProxyItem, flag: str) -> str:
    return f'{flag} https://t.me/proxy?server={item.server}&port={item.port}&secret={item.secret}'

def format_dead(item: ProxyItem, flag: str) -> str:
    return f'{flag} https://t.me/proxy?server={item.server}&port={item.port}&secret={item.secret}'



# -- -- -- Основная функция -- -- -- #
def main():
    proxies = asyncio.run(fetch_proxies())
    total = len(proxies)

    working_mtproxy = []
    dead_mtproxy = []

    for i, item in enumerate(proxies, 1):
        country = get_flag(item.server)
        ok, ms = check_connection(item)

        if ok:
            working_mtproxy.append((item, country, ms))
            print(f"[{i}/{total}] [{country}] [WORK] [{ms} ms] -> {item.server}:{item.port}")
        else:
            dead_mtproxy.append((item, country, ms))
            print(f"[{i}/{total}] [{country}] [DEAD] [0 ms] -> {item.server}:{item.port}")

    with open(FILE_WORKING_MTPROXY, "w", encoding="utf-8") as f:
        for item, country, ms in working_mtproxy:
            f.write(format_working(item, country) + "\n")

    with open(FILE_DEAD_MTPROXY, "w", encoding="utf-8") as f:
        for item, country, error in dead_mtproxy:
            f.write(format_dead(item, country) + "\n")

    print("\nDONE")
    update_readme()



def update_readme():
    with open(FILE_WORKING_MTPROXY, "r", encoding="utf-8") as f:
        proxies = f.read().strip().split("\n")

    proxies_text = "\n".join(
    f"[MTProxy {i+1}]({p})"
    for i, p in enumerate(proxies[:100])
    )

    content = f"""# MTProxy list

Обновляется каждые 30 минут.


## Working proxies

```
{proxies_text}
```
"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)



if __name__ == '__main__':
    main()