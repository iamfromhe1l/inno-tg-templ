import logging
from aiogram import Bot, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.webhook import SendMessage
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
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

def get_keybd():
    buttons = [
        types.InlineKeyboardButton(text='-1', callback_data='num_dec'),
        types.InlineKeyboardButton(text='+1', callback_data='num_inc'),
        types.InlineKeyboardButton(text='Done', callback_data='num_fnsh'),
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    return keyboard

async def update_text(msg: types.Message, new_value: int):
    await msg.edit_text(f'Укажите число: {new_value}', reply_markup=get_keybd())

@dp.message_handler(commands='numbers')
async def cmd_nums(msg: types.Message):
    user_data[msg.from_user.id] = 0
    await msg.answer('Укажите число: 0', reply_markup=get_keybd())

@dp.callback_query_handler(Text(startswith='num_'))
async def call_num(call: types.CallbackQuery):
    user_val = user_data.get(call.from_user.id, 0)
    action = call.data.split('_')[1]
    if action == 'incr':
        user_data[call.from_user.id] = user_val + 1
        await update_text(call.message, user_val+1)
    elif action == 'decr':
        user_data[call.from_user.id] = user_val - 1
        await update_text(call.message, user_val - 1)
    elif action == 'finish':
        await call.message.edit_text(f'Итого: {user_val}')
    await call.answer()

async def on_startup(dp):
    await bot.set_webhook((wh_url))
    
async def on_shutdown(dp):
    logging.warning('turning off')
    
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_close()
    
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