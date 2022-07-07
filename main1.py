from aiogram import Bot, types, Dispatcher
import requests
from aiogram.utils.executor import start_webhook
from bs4 import BeautifulSoup as bs
import asyncio
import aioschedule
import os
import logging

TOKEN = os.getenv('BOT_TOKEN')
URL = os.getenv('URL')
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

wh_host = f'https://{HEROKU_APP_NAME}.herokuapp.com'
wh_path = f'/webhook/{TOKEN}'
wh_url = f'{wh_host}{wh_path}'

user_data = {}
whapp_host = '0.0.0.0'
whapp_port = os.getenv('PORT', default=8000)

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher(bot)
chatid = '933028899'

def getCurses(URL):
    r = requests.get(URL)
    soup = bs(r.text, "html.parser")
    divs = soup.find_all("div", {'class':'my-1'})
    mas = []
    for e in divs:
        res = e.text
        res = res.replace('  ', '').replace('\r', '').replace('\n\n', '')
        mas.append(res.split('\n'))
    return mas

def getResult(mas):
    result = ''
    sub_res = mas
    for elem in sub_res:
        result += ': '.join(elem) + '\n'
    return result


@dp.message_handler()
async def sch_r():
    res = getResult(getCurses(URL))
    await bot.send_message(chat_id=chatid, text=res)

async def scheduler():
    aioschedule.every().hour.do(sch_r)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(dp):
    asyncio.create_task(scheduler())

async def on_shutdown(dp):
    logging.warning('turning off')
    
    await bot.delete_webhook()
    await dp.storage.close()
    
    logging.warning('bye')

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=wh_path,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=whapp_host,
        port=whapp_port
    )