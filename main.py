import asyncio
import os.path
import time
import socks
from configparser import ConfigParser
from nest_asyncio import apply
import telethon
from loguru import logger
from telethon import TelegramClient
from telethon import functions
from telethon.errors import FloodWaitError, InvalidBufferError, AuthKeyError, AuthKeyNotFound, UsernameInvalidError
from datetime import datetime
apply()
current_session_time = datetime.now()
logger.add("log.txt", level="DEBUG")

try:
    config = ConfigParser()
    config.read("config.ini", encoding="utf-8")
    delay_from = int(config["DELAY"]["delay"])
    proxy = config["PROXY"]["proxy"]
    path_to_usernames = config["PATH_TO_TXT"]["path_to_usernames"]
    session_name = config["SESSION"]["name_session"]
    if not(os.path.exists(path_to_usernames) and os.path.isfile(path_to_usernames)):
        raise TypeError(f"Не нашел файла - {path_to_usernames}")
    with open("busy.txt", "w", encoding="utf-8") as busy_file:
        pass
    with open("free.txt", "w", encoding="utf-8") as free_file:
        pass
except TypeError as ex:
    raise TypeError(ex.args[0])
except Exception as ex:
    raise ValueError("Не все переменные конфига заполнены!")


def read_usernames():
    usernames = []
    with open(path_to_usernames) as usernames_file:
        lines = usernames_file.readlines()
        for line in lines:
            if line.strip():
                usernames.append(line.strip())
    return usernames


async def main():
    global proxy
    if proxy == "None":
        proxies = {}
    else:
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}',
        }
    counter = 0
    usernames = read_usernames()
    all_usernames = len(usernames)
    client = TelegramClient(session=session_name, api_id=13118630, api_hash="2e2996b8a26cc901f33d179999c7f1e8")
    is_connected = False
    try:
        await client.connect()
        await client.start()
        is_connected = True

    except InvalidBufferError:
        await client.disconnect()
        logger.error("Не смог подключиться к аккаунту!")
        return
    except AuthKeyNotFound:
        await client.disconnect()
        logger.info(
            f"Аккаунт потерял ключ аутентификации, отправляю его в badsessions, количество подписок - ")
        return
    except AuthKeyError:
        await client.disconnect()
        logger.error(
            f"Аккаунт запущен на 2-х разных ip")
        return
    except telethon.errors.TypeNotFoundError:
        await client.disconnect()
        print('Телеграмм отправил старый объект')

    while len(usernames) > 0 and is_connected:
        username = usernames.pop(0)
        time_delta = (datetime.now() - current_session_time).total_seconds()
        hours = int(time_delta / 3600)
        minutes = int((time_delta - hours * 3600) / 60)
        seconds = int((time_delta - hours * 3600 - minutes * 60))
        try:

            result = await client(functions.account.CheckUsernameRequest(username=username))
            counter += 1
            if result:
                with open("free.txt", "a", encoding="utf-8") as free_file:
                        free_file.write(f"{username}\n")
                logger.success(f"Юзернейм - {username} свободен! Обработано - {counter}/{all_usernames} юзернеймов! Осталось обработать - {len(usernames)} | В данной сессии - {hours}:{minutes}:{seconds}")
            else:
                with open("busy.txt", "a", encoding="utf-8") as busy_file:
                    busy_file.write(f"{username}\n")
                logger.info(f"Юзернейм - {username} занят! Обработано - {counter}/{all_usernames} юзернеймов! Осталось обработать - {len(username)} | В данной сессии - {hours}:{minutes}:{seconds}")
            with open(path_to_usernames, "w") as usernames_file:
                for username in usernames:
                    usernames_file.write(f"{username}\n")
            time.sleep(delay_from / 1000)
        except FloodWaitError as flood:
            await client.disconnect()
            sec = flood.seconds
            logger.error(f"Словил флуд на {sec} секунд.. Ожидаю {sec} секунд....")
            time.sleep(sec + 10)
        except UsernameInvalidError:
            logger.error(
                f"Юзернейм - {username} невалид! Обработано - {counter}/{all_usernames} юзернеймов! Осталось обработать - {len(usernames)} | В данной сессии - {hours}:{minutes}:{seconds}")

            with open(path_to_usernames, "w") as usernames_file:
                for username in usernames:
                    usernames_file.write(f"{username}\n")
            with open("busy.txt", "a", encoding="utf-8") as busy_file:
                busy_file.write(f"{username}\n")
            counter += 1
            time.sleep(delay_from / 1000)
        except Exception as ex:
            logger.error(f"{username} - произошла непредвиденная ошибка")
            print(ex)
            time.sleep(5)
    logger.success("Закончил обработку юзернеймов!")


if __name__ == "__main__":
    asyncio.run(main())
    input("Нажми enter для выхода...")