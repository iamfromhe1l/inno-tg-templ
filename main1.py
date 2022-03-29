import logging
from aiogram import Bot, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.webhook import SendMessage
from random import randint

import aiogram.utils.markdown as md
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode


from aiogram.utils.executor import start_webhook
import os

TOKEN = os.getenv('BOT_TOKEN')
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

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



# States
class Form(StatesGroup):
    in_game = State()
    not_in_game = State()
    stt_state = State()

async def cmd_start(message: types.Message, state: FSMContext):
    await Form.in_game.set()
    async with state.proxy() as data:
        data['rand_num'] = randint(1,10)
    await bot.send_message(text='Я загадал число от 1 до 10',chat_id=message.from_user.id)


@dp.message_handler(commands='start', state=[Form.not_in_game, '*'])
async def start(message: types.Message, state: FSMContext):
    await cmd_start(message, state)

@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.in_game)
async def int_error(message: types.Message):
    return await message.reply(text='Нужно ввести число!')

@dp.message_handler(lambda message: message.text.isdigit(), state=Form.in_game)
async def usr_num(message: types.Message, state: FSMContext):
    num = int(message.text)
    async with state.proxy() as data:
        rand_num = data['rand_num']
        if num > rand_num:
            await message.reply(text='Меньше')
        elif num < rand_num:
            await message.reply(text='Больше')
        else:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text='Сыграть ещё раз', callback_data='restart'))
            keyboard.add(types.InlineKeyboardButton(text='Пожилой Алигатор', callback_data='alia'))
            await message.reply(text='Ура, ты выйграл', reply_markup=keyboard)
            await Form.not_in_game.set()

@dp.callback_query_handler(text='restart', state=Form.not_in_game)
async def restart_game(message: types.Message, state: FSMContext):
    await cmd_start(message=message, state=state)

@dp.callback_query_handler(text='alia', state=Form.not_in_game)
async def alia(call: types.CallbackQuery, state: FSMContext):
    await bot.send_photo(chat_id=call.from_user.id, photo='https://i.kym-cdn.com/entries/icons/facebook/000/035/259/Cursed_Image_Compilations_Thumbnail.jpg', caption='Здарова славяне!!!')

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
