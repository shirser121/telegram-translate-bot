import translators as ts
from telethon import TelegramClient, functions, events, sync
import asyncio
import requests

# Telegram API

chat_to_send = "chat_to_send"
chat = chat_to_send
manager_chat = "manager_chat"

session_name = 'session_name'
api_id = '*****'
api_hash = '*****'
client = TelegramClient(session_name, api_id, api_hash)

block = False
disconnect = False


async def loop():
    await asyncio.sleep(10)
    if disconnect == True:
        await client.disconnect()


async def start_client():
    global block
    global disconnect
    async with client:
        while True:
            block = False

            @client.on(events.NewMessage(chats=[manager_chat], incoming=True))
            async def handler(event):
                try:
                    text = event.message.message
                    if text.lower() == "reset":
                        await event.reply('Ok...')
                        block = True
                        await asyncio.sleep(10)
                        await event.reply("Reset")
                        # await client.disconnect()
                        disconnect = True
                except Exception as e:
                    print("Error", e)

            @client.on(events.NewMessage(incoming=True))
            async def handler(event):
                global block
                try:
                    if block == True:
                        return
                    # print(event)
                    # print("\n\n")
                    asyncio.create_task(sendMessage(event))
                except Exception as e:
                    print("Error", e)

            await client.connect()

            async for dialog in client.iter_dialogs():
                if dialog.is_channel:
                    print(f'{dialog.id}:{dialog.title}')

            await client.send_message(chat, "Started", parse_mode='html')

            while disconnect == False:
                await asyncio.sleep(10)

            print("Restarting")


def translate(text):
    # from_language="auto",
    def sogou_translate(text):
        return ts.sogou(text, timeout=15, to_language="he")

    def backup_bing_translate(text):
        return ts.bing(text, timeout=15, from_language="ar", to_language="he")

    def backup_google_translate(text):
        return ts.google(text, timeout=15, from_language="ar", to_language="iw")

    def bing_translate(text):
        params = {"fromLang": "ar", "to": "he", "text": text}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
            'Referer': 'https://www.bing.com/translator'}
        json_res = requests.post(
            "https://www.bing.com/ttranslatev3?isVertical=1&&IG=A64692BA2B2A4A8BA54A3748DB5901E6&IID=translator.5026.11",
            data=params, headers=headers, timeout=15).json()
        return "b: " + json_res["translations"][0]["text"]

    def google_translate(text):
        params = {"client": "gtx", "dt": "t", "sl": "ar", "tl": "iw", "q": text}
        json_res = \
            requests.get(f"https://translate.googleapis.com/translate_a/single", params=params, timeout=15).json()[0]
        return "".join([line[0] for line in json_res])

    try:
        return bing_translate(text)
    except Exception:
        try:
            return google_translate(text)
        except Exception:
            try:
                return backup_google_translate(text)
            except Exception:
                try:
                    return backup_bing_translate(text)
                except Exception:
                    return ""  # sogou_translate(text)


async def sendMessage(event):
    try:
        text = event.message.message
        if len(text) == 0:
            return

        translatedText = ""
        try:
            translatedText = translate(text)
            translatedText = translatedText.replace("&#10;", "").replace("דחוף|דחוף", "")
        except Exception as e:
            print("Error", e)
            translatedText = "התרגום לא הצליח"

        link = ""
        try:
            chat_from = event.chat if event.chat else (await event.get_chat())  # telegram MAY not send the chat enity
            # print(chat_from)
            chat_title = chat_from.title if hasattr(chat_from,
                                                    'title') else chat_from.first_name + " " + chat_from.last_name
            chat_username = chat_from.username
            if chat_title:
                link += "<b>ערוץ:</b> " + chat_title + "\n"
            if chat_username:
                link += "https://t.me/" + chat_username + "/" + str(event.message.id) + "/"
        except Exception as e:
            print("Error chat", e)

        string_message = translatedText
        string_message += "\n\n<b>מקור:</b> " + text + "\n\n" + link
        string_message = string_message.replace("\n", "<pre>\n</pre>")

        await client.send_message(chat, string_message, parse_mode='html')


    except Exception as e:
        print(e)
        pass


def main():
    print("Translate arabic channels\n")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_client())
    loop.close()


if __name__ == '__main__':
    main()
