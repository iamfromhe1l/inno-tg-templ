import logging
from aiogram import Bot, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.webhook import SendMessage
<<<<<<< HEAD
import requests
from datetime import datetime
=======
from random import randint
>>>>>>> 426fa05456a1a35df4da17e877ad91264bf753e8

import aiogram.utils.markdown as md
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode


from aiogram.utils.executor import start_webhook
import os

TOKEN = os.getenv('BOT_TOKEN')
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')
WEATHER_API = os.getenv('WEATHER_API')

wh_host = f'https://{HEROKU_APP_NAME}.herokuapp.com'
wh_path = f'/webhook/{TOKEN}'
wh_url = f'{wh_host}{wh_path}'

user_data = {}
whapp_host = '0.0.0.0'
whapp_port = os.getenv('PORT', default=8000)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
storage = MemoryStorage()

dp = Dispatcher(bot,storage=storage)
dp.middleware.setup(LoggingMiddleware())


def get_weather(city, weather_api):
    API_LINK = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api}&units=metric'
    r = requests.get(API_LINK)
    return r.json(), r.status_code

def city_check(city, weather_api):
    status = get_weather(city, weather_api)[1]
    return 0 if status != 200 else 1

def decode_weather(w):
    res = []
    wm=w['main']
    res.append(f'Город: {w["name"]}\n')
    res.append(f'Температура:\n1.Current: {wm["temp"]}°С, 2.Max: {wm["temp_max"]}°С, 3.Min: {wm["temp_min"]}°С\n')
    res.append(f'Влажность: {wm["humidity"]}%\n')
    tzsec = w['timezone']
    sunrise_t = datetime.utcfromtimestamp(w["sys"]["sunrise"]+tzsec).strftime('%Y-%m-%d %H:%M:%S')
    sunset_t = datetime.utcfromtimestamp(w["sys"]["sunset"]+tzsec).strftime('%Y-%m-%d %H:%M:%S')
    res.append(f'Время рассвета: {sunrise_t.split()[1]}\nВремя заката: {sunset_t.split()[1]}')
    return '\n'.join(res)

class Form(StatesGroup):
    get_city = State()
    main_st = State()

@dp.message_handler(commands='start', state='*')
async def get_city_name(message: types.Message):
    await Form.get_city.set()
    await message.answer(text='Введите название города', reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(lambda message: not city_check(message.text, WEATHER_API), state=Form.get_city)
async def wrong_city(message: types.Message):
    await message.reply(text='Вы ввели неправильный город')

@dp.message_handler(lambda message: city_check(message.text, WEATHER_API), state=Form.get_city)
async def set_city(message: types.Message, state=FSMContext):
    await Form.main_st.set()
    city = message.text
    kbd= types.ReplyKeyboardMarkup()
    btn = types.KeyboardButton('Вывести погоду')
    kbd.add(btn)
    async with state.proxy() as data:
        data['def_city'] = city
        await message.reply(text='Город по умолчанию установлен\nВведите /start, чтобы выбрать другой город', reply_markup=kbd)

@dp.message_handler(text='Вывести погоду', state=Form.main_st)
async def print_weather(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        await message.answer(decode_weather(get_weather(data['def_city'],WEATHER_API)[0]))

async def on_startup(dp):
    await bot.set_webhook((wh_url))
    
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
