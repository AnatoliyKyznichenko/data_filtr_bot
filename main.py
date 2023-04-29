import csv
import json

import pyexcel_xlsx
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import logging
from dotenv import dotenv_values
from config import config_file
from aiogram import types
from datetime import datetime

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=config_file['token'])
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands='start')
async def file_user(message: types.Message):
    await storage.set_state(chat=message.chat.id, state='file')
    await message.answer('Отправьте файл с данными: ')


@dp.message_handler(state='file', content_types=['document'])
async def start(message: types.Message):
    await message.document.download(destination=str(message.chat.id) + '.csv') # destination место куда его сохрать
    await storage.set_state(chat=message.chat.id, state='one')
    await message.answer('Введите минимальный возраст клиентов: ')


@dp.message_handler(state='one')
async def number(message: types.Message, state: FSMContext):
    await state.update_data(data={'number': int(message.text)})
    await state.set_state(state='two')
    await message.answer('Введите максимальный возраст клиентов: ')


@dp.message_handler(state='two')
async def age(message: types.Message, state: FSMContext):
    state_data = await state.get_data() # получили дату из state (тут пока что хранится только мин возраст, макс возраст это message.text)
    data = list() # тут все данные из csv файла
    # открываем файл
    with open(str(message.chat.id) + '.csv', newline='', encoding='utf-8') as csvfile:
        csv_data = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in csv_data:
            data.append(row)
    filtered_age = date_filter(data, (state_data['number'], int(message.text))) # фильтруем по возрасту все данные
    availiable = set([i[5] for i in filtered_age]) # список городов
    # убираем "" из сета
    while "" in availiable:
        availiable.remove("")
    result_value = dict()
    for town in availiable:
        result_value[town] = len([i for i in filtered_age if i[5] == town])
    string_format = "".join((f"{region}: {value}\n" for region, value in result_value.items()))
    await message.answer(f"Введите регион клиентов(или \"любой\" другой микса)\nДоступные:{string_format}")
    await state.update_data(data={'age': int(message.text)}) # макс возраст записываем в дату
    await state.set_state(state='three') # следующий state


@dp.message_handler(state='three')
async def number(message: types.Message, state: FSMContext):
    state_data = await state.get_data() # получили дату из state (тут пока что хранится только мин возраст, макс возраст это message.text)
    data = list() # тут все данные из csv файла
    # открываем файл
    with open(str(message.chat.id) + '.csv', newline='', encoding='utf-8') as csvfile:
        csv_data = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in csv_data:
            data.append(row)
    filtered_prev = data_filter_user(date_filter(data, (state_data['number'], state_data['age'])), 5, message.text)
    # print(json.dumps(filtered_prev, ensure_ascii=False, indent=2))
    result_value = dict()
    result_value['да'] = len([i for i in filtered_prev if i[7] == 'восток'])
    result_value['нет'] = len([i for i in filtered_prev if i[7] != 'восток'])
    result_string = f"да: {result_value['да']}\nнет: {result_value['нет']}\nлюбой: {result_value['да'] + result_value['нет']}"
    await message.answer(f"Введите регион клиентов(или \"любой\" другой микса)\nДоступные:\n{result_string}")
    await state.update_data(data={'client': message.text})
    await state.set_state(state='four')
    await message.answer('Выберите клиентов с востока (да/нет/любой): ')


@dp.message_handler(state='four')
async def number(message: types.Message, state: FSMContext):
    state_data = await state.get_data() # получили дату из state (тут пока что хранится только мин возраст, макс возраст это message.text)
    data = list() # тут все данные из csv файла
    # открываем файл
    with open(str(message.chat.id) + '.csv', newline='', encoding='utf-8') as csvfile:
        csv_data = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in csv_data:
            data.append(row)
    filtered_prev = data_filter_user(date_filter(data, (state_data['number'], state_data['age'])), 5, message.text)
    vostok_client = message.text
    if vostok_client in ['да', 'нет']:
        r = data_filter_user(filtered_prev, 7, 'восток')
        if vostok_client == 'да':
            filtered_prev = r
        else:
            filtered_prev = [i for i in filtered_prev if i not in r]
    print(json.dumps(filtered_prev, ensure_ascii=False, indent=2))
    availiable = set([i[4] for i in filtered_prev])
    print(availiable)
    result_value = dict()
    for value in availiable:
        result_value[value] = len([i for i in filtered_prev if i[4] == value])
    result_string = "".join([f"{op}: {c}" for op, c in result_value.items()])
    await state.update_data(data={'messager': message.text})
    await state.set_state(state='five')
    await message.answer(f'Выберите клиентов с Ватсапом (да/нет/любой)\nДоступные:\n{result_string}')


@dp.message_handler(state='five')
async def number(message: types.Message, state: FSMContext):
    await state.update_data(data={'number_operator': message.text})
    await state.set_state(state='six')
    await message.answer('Введите номера операторов через запятую: ')


@dp.message_handler(state='six')
async def number(message: types.Message, state: FSMContext):
    await state.update_data(data={'save_user': message.text})
    await state.set_state(state='seven')
    await message.answer('Введите количество клиентов для сохранения: ')


@dp.message_handler(state='seven')
async def count_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    rm = []
    with open(str(message.chat.id) + '.csv', newline='', encoding='utf-8') as csvfile:
        csv_data = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in csv_data:
            rm.append(row)

    age = data['number'], data['age']
    vostok_client = data['messager']
    if vostok_client in ['да', 'нет']:
        r = data_filter_user(rm, 7, 'восток')
        if vostok_client == 'да':
            rm = r
        else:
            rm = [i for i in rm if i not in r] # убираем все вхождения строк у которых нет востока

    whatsApp = data['number_operator']
    if whatsApp in ['да', 'нет']:
        r = data_filter_user(rm, 8, 'ватсап')
        if whatsApp == 'да':
            rm = r
        else:
            rm = [i for i in rm if i not in r]

#фильтрация регионов

    city = data['client']
    if city != 'любой':
        rm = data_filter_user(rm, 5, city)

    rm = date_filter(rm, age)
    rm = provider_filter(rm, data['save_user'].split(','))
    await message.answer(json.dumps(rm[0:int(message.text)], ensure_ascii=False, indent=2)) #0:int(message.text) так как это последнее состояние
    # ensure_ascii=False для кирилицы
    await state.finish()

'''Принимаем список в котором данные в списковом формате, индекс под каким данные, info что за данные хотим получать'''


def data_filter_user(data: list[list], index, info):
    result = []
    for item in data:
        if item[index] == info:
            result.append(item)
    return result


'''Фильтр получения возраста'''


def date_filter(data, ranges: tuple):
    time = []
    now = datetime.now()
    begin, end = ranges
    for i in data:
        if now.year - datetime.strptime(i[3], '%d.%m.%Y').year in range(begin, end+1):
            time.append(i)
    return time


'''Фильтр провайдер'''


def provider_filter(data, operator):
    res = []
    for i in data:
        if i[4] in operator:
            res.append(i)
    return res


if __name__ == '__main__':
    executor.start_polling(dp)
