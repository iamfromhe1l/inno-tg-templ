from aiogram import Bot, types, Dispatcher
import requests
from aiogram.utils.executor import start_webhook
from bs4 import BeautifulSoup as bs
import asyncio
import aioschedule
import os
import logging
import traceback
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

TOKEN = os.getenv('BOT_TOKEN')
VK_TOKEN = os.getenv('VK_TOKEN')
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
chatid = -1001695478512

main_token = VK_TOKEN
vs = vk_api.VkApi(token=main_token)
lp = VkBotLongPoll(vs, 216087336)

async def vkPooling(sleepSec, getInfo):
    while True:
        await asyncio.sleep(sleepSec)
        try:
            for ev in lp.listen():
                toJson = {'main': {'text': '', 'url': []}, 'forward': {'text': '', 'url': []}, 'reply': {'text': '', 'url': []}}
                if ev.type==VkBotEventType.MESSAGE_NEW:
                    if ev.from_chat:
                        mainObj=ev.object.message
                        mainText=mainObj['text']
                        mainAtt=mainObj['attachments']
                        frwObj=ev.object.message['fwd_messages']
                        try:
                            repObj=ev.object.message['reply_message']
                        except:
                            repObj={'text': '', 'url': []}
                        if '@all' in mainText:
                            toJson = getInfo(mainText,mainAtt,'main', toJson)
                            if len(frwObj) != 0:	
                                frwText=frwObj[0]['text']
                                frwAtt=frwObj[0]['attachments']
                                toJson = getInfo(frwText, frwAtt,'forward', toJson)
                            try:
                                if len(repObj) != 0:	
                                    repText=repObj['text']
                                    repAtt=repObj['attachments']
                                    toJson = getInfo(repText, repAtt,'reply', toJson)
                            except:
                                pass
                            
                            mainText = toJson['main']['text']
                            replyText = toJson['reply']['text']
                            forwardText = toJson['forward']['text']
                            allUrls = toJson['main']['url']
                            addMain = f'Основное сообщение: \n {mainText} \n'
                            addForward = ''
                            if forwardText != '':
                                addForward = f'Пересланное сообщение: \n {forwardText} \n'
                                allUrls.extend(toJson['forward']['url'])
                            addReply = ''
                            if replyText != '':
                                addReply = f'Ответ на сообщение: \n {replyText} \n'
                                allUrls.extend(toJson['reply']['url'])
                            await bot.send_message(chat_id=chatid, text=f'{addMain} \n {addReply} \n {addForward}')
                            if len(allUrls) > 1:
                                media = types.MediaGroup()
                                for img in allUrls:
                                    media.attach_photo(img, '')
                                await bot.send_media_group(chat_id=chatid,media=media)
                            else:
                                for img in allUrls:
                                    await bot.send_photo(chat_id=chatid, photo=img)
                            toJson = {'main': {'text': '', 'url': []}, 'forward': {'text': '', 'url': []}, 'reply': {'text': '', 'url': []}}
        except:
            print('error')
            await asyncio.sleep(3)

def getInfo(msg, att, whoSent, ToJson):
    toJson = ToJson
    for i in range(len(msg)):
        if msg[i]=='@' and msg[i+1]=='a':
            msg = msg[:i] + msg[i+5:]
            break
    toJson[whoSent]['text'] = msg
    if att!=[]:
        toJson[whoSent]['url'] = list()
        for i in range(len(att)):
            if att[0]['type']=='photo':
                photoSizes = att[i]['photo']['sizes']
                photoSizes.sort(key=lambda x: x['height'])
                bestQuality = photoSizes[-1]['url']
            else:
                bestQuality = att[i]['url']
            toJson[whoSent]['url'].append(bestQuality)
    else:
        toJson[whoSent]['url'] = []
    return toJson

async def on_startup(dp):
    asyncio.create_task(vkPooling(10, getInfo))


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
