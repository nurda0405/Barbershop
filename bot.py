import gspread, logging
from google.oauth2.service_account import Credentials
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
import asyncio, threading

app = Flask(__name__)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file('', scopes = scope)
client = gspread.authorize(creds)

spreadsheet = client.open('Барбершоп')
worksheets = spreadsheet.worksheets()
days = [worksheet.title for worksheet in worksheets]

days_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=day, callback_data=f'show_hours_{day}') for day in days], [InlineKeyboardButton(text = '🔄', callback_data='update_days')]])

hours_markup = {}

for day in worksheets:
    hours = day.get_all_records()
    free_hours = []

    for hour in hours:
        if hour['Статус'] == 'Бос':
            free_hours.append(hour['Сағат'])

    
    keyboard = []

    for i in range(len(free_hours)//3):
        row = [InlineKeyboardButton(text = free_hours[i], callback_data='.'), InlineKeyboardButton(text = free_hours[i + len(free_hours)//3], callback_data='.'), InlineKeyboardButton(text = free_hours[i + 2*len(free_hours)//3], callback_data='.')]
        keyboard.append(row)
    
    if len(free_hours) == 0:
        keyboard.append([InlineKeyboardButton(text = 'Бұл күнге бос уақыттар бітті', callback_data='.')])
    keyboard.append([InlineKeyboardButton(text = '🔄', callback_data=f'update_hours_{day.title}')])
    keyboard.append([InlineKeyboardButton(text = '📞', callback_data='.')]) #url = 'tel:+77750091095',
    keyboard.append([InlineKeyboardButton(text = '⬅️', callback_data='go_back')])

    hours_markup[day.title] = InlineKeyboardMarkup(inline_keyboard=keyboard)


bot = Bot(token = '')
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

@dp.message(Command('start'))
async def show_dates(message:types.Message):
    await bot.send_message(chat_id = message.from_user.id, text = 'Қош келдіңіз! Күнді таңдаңыз:', reply_markup=days_markup)

@dp.message()
async def delete_message(message: types.Message):
    await message.delete()

@dp.callback_query(lambda c: c.data == 'update_days')
async def update_dates(callback_query: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, reply_markup=days_markup)

@dp.callback_query(lambda c: c.data.startswith('update_hours'))
async def update_dates(callback_query: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, reply_markup=hours_markup[callback_query.data.split('_')[2]])

@dp.callback_query(lambda c: c.data.startswith('show_hours'))
async def show_hours(callback_query: types.CallbackQuery):
    date = callback_query.data.split('_')[2]
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text = f'{date} күніне бос уақыттар', reply_markup=hours_markup[callback_query.data.split('_')[2]])

@dp.callback_query(lambda c: c.data == 'go_back')
async def update_dates(callback_query: types.CallbackQuery):
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text = 'Қош келдіңіз! Күнді таңдаңыз:', reply_markup=days_markup)

@app.route('/update', methods = ['POST'])
def update_data():
    global client, days_markup, hours_markup
    spreadsheet = client.open('Барбершоп')
    worksheets = spreadsheet.worksheets()
    days = [worksheet.title for worksheet in worksheets]

    days_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=day, callback_data=day) for day in days], [InlineKeyboardButton(text = '🔄', callback_data='update_days')]])

    hours_markup = {}

    for day in worksheets:
        hours = day.get_all_records()
        free_hours = []

        for hour in hours:
            if hour['Статус'] == 'Бос':
                free_hours.append(hour['Сағат'])

        
        keyboard = []

        for i in range(len(free_hours)//3):
            row = [InlineKeyboardButton(text = free_hours[i]), InlineKeyboardButton(text = free_hours[i + len(free_hours)//3]), InlineKeyboardButton(text = free_hours[i + 2*len(free_hours)//3])]
            keyboard.append(row)
        
        if len(free_hours) == 0:
            keyboard.append([InlineKeyboardButton(text = 'Бұл күнге бос уақыттар бітті')])
        keyboard.append([InlineKeyboardButton(text = '🔄', callback_data=f'update_hours_{day.title}')])
        keyboard.append([InlineKeyboardButton(text = '📞', url = 'tel:+77750091095')])
        keyboard.append([InlineKeyboardButton(text = '⬅️', callback_data='go_back')])

        hours_markup[day.title] = InlineKeyboardMarkup(inline_keyboard=keyboard)

async def main():
    await dp.start_polling(bot)

def run_flask():
    app.run(host='0.0.0.0', port = 5000)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    asyncio.run(main())