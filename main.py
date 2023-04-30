import csv
import os

import openpyxl

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import logging
from config import config_file
from aiogram import types
from datetime import datetime

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=config_file['token'])
dp = Dispatcher(bot, storage=storage)
data_filename = "test.csv"
outfile_filename = "all_result.csv"


def is_allowed(msg: types.Message):
    with open("allowed_id.txt") as file:
        data = file.read()
    return str(msg.from_user.id) in data.split("\n")


@dp.message_handler(is_allowed, commands='start')
async def file_user(message: types.Message):
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
    with open(data_filename, newline='', encoding='utf-8') as csvfile:
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
    await state.update_data(data={'age': int(message.text)})  # макс возраст записываем в дату
    await state.set_state(state='three')  # следующий state


@dp.message_handler(state='three')
async def number(message: types.Message, state: FSMContext):
    state_data = await state.get_data() # получили дату из state (тут пока что хранится только мин возраст, макс возраст это message.text)
    data = list() # тут все данные из csv файла
    # открываем файл
    with open(data_filename, newline='', encoding='utf-8') as csvfile:
        csv_data = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in csv_data:
            data.append(row)
    filtered_prev = data_filter_user(date_filter(data, (state_data['number'], state_data['age'])), 5, message.text)
    result_value = dict()
    result_value['да'] = len([i for i in filtered_prev if i[7] == 'восток'])
    result_value['нет'] = len([i for i in filtered_prev if i[7] != 'восток'])
    result_string = f"да: {result_value['да']}\nнет: {result_value['нет']}\nлюбой: {result_value['да'] + result_value['нет']}"
    await message.answer(f"Введите клиентов с востока (да/нет/любой)\nДоступные:\n{result_string}")
    await state.update_data(data={'client': message.text})
    await state.set_state(state='four')


@dp.message_handler(state='four')
async def number(message: types.Message, state: FSMContext):
    state_data = await state.get_data() # получили дату из state (тут пока что хранится только мин возраст, макс возраст это message.text)
    data = list() # тут все данные из csv файла
    # открываем файл
    with open(data_filename, newline='', encoding='utf-8') as csvfile:
        csv_data = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in csv_data:
            data.append(row)
    filtered_prev = date_filter(data, (state_data['number'], state_data['age']))
    if state_data['client'] != 'любой':
        filtered_prev = data_filter_user(filtered_prev, 5, state_data['client'])
    vostok_client = message.text
    if vostok_client in ['да', 'нет']:
        r = data_filter_user(filtered_prev, 7, 'восток')
        if vostok_client == 'да':
            filtered_prev = r
        else:
            filtered_prev = [i for i in filtered_prev if i not in r]
    availiable = set([i[4] for i in filtered_prev])
    result_value = dict()
    result_value['да'] = len([i for i in filtered_prev if i[8] == 'ватсап'])
    result_value['нет'] = len([i for i in filtered_prev if i[8] != 'ватсап'])
    result_string = f"да: {result_value['да']}\nнет: {result_value['нет']}\nлюбой: {result_value['да'] + result_value['нет']}"
    await state.update_data(data={'messager': message.text})
    await state.set_state(state='five')
    await message.answer(f'Выберите клиентов с Ватсапом (да/нет/любой)\nДоступные:\n{result_string}')


@dp.message_handler(state='five')
async def number(message: types.Message, state: FSMContext):
    state_data = await state.get_data() # получили дату из state (тут пока что хранится только мин возраст, макс возраст это message.text)
    data = list() # тут все данные из csv файла
    # открываем файл
    with open(data_filename, newline='', encoding='utf-8') as csvfile:
        csv_data = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in csv_data:
            data.append(row)
    filtered_prev = date_filter(data, (state_data['number'], state_data['age']))
    if state_data['client'] != 'любой':
        filtered_prev = data_filter_user(filtered_prev, 5, state_data['client'])
    vostok_client = state_data['messager']
    if vostok_client in ['да', 'нет']:
        r = data_filter_user(filtered_prev, 7, 'восток')
        if vostok_client == 'да':
            filtered_prev = r
        else:
            filtered_prev = [i for i in filtered_prev if i not in r]

    whatsapp = message.text
    if whatsapp in ['да', 'нет']:
        r = data_filter_user(filtered_prev, 8, 'ватсап')
        if whatsapp == 'да':
            filtered_prev = r
        else:
            filtered_prev = [i for i in filtered_prev if i not in r]

    availiable = set([i[4] for i in filtered_prev])
    result_value = dict()
    for value in availiable:
        result_value[value] = len([i for i in filtered_prev if i[4] == value])
    result_string = "".join([f"{op}: {c}\n" for op, c in result_value.items()])
    await state.update_data(data={'number_operator': message.text})
    await state.set_state(state='six')
    await message.answer(f'Введите номера операторов через запятую\nДоступные:\n{result_string}')


@dp.message_handler(state='six')
async def number(message: types.Message, state: FSMContext):
    await state.update_data(data={'save_user': message.text})
    await state.set_state(state='seven')
    await message.answer('Введите количество клиентов для сохранения: ')


@dp.message_handler(state='seven')
async def count_user(message: types.Message, state: FSMContext):
    await message.answer("Введите название файла, куда сохранять данные")
    await state.update_data(data={"count_users": int(message.text)})
    await state.set_state("filename")


@dp.message_handler(state='filename')
async def get_filename(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.answer("Текущие фильтры:\n"
                         f"Возраст: {data['age']} - {data['number']}\n"
                         f"Регион: {data['client']}\n"
                         f"Операторы: {data['save_user']}\n"
                         f"Ватсап: {data['number_operator']}\n"
                         f"Восток: {data['messager']}\n"
                         f"Количество клиентов: {data['count_users']}\n"
                         "Вы уверенны, что хотите получить данные?(да/нет)"
                         )
    await state.update_data(data={"filename": message.text})
    await state.set_state("confirm")


@dp.message_handler(state='confirm')
async def count_user(message: types.Message, state: FSMContext):
    if message.text != "да":
        await message.answer("отмена фильтров. Начинаем заново")
        await message.answer('Введите минимальный возраст клиентов: ')
        await state.finish()
        await state.set_state("one")
        return
    data = await state.get_data()
    rm = []
    with open(data_filename, newline='', encoding='utf-8') as csvfile:
        csv_data = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in csv_data:
            rm.append(row)

    rm = date_filter(rm, (data['number'], data['age']))

    city = data['client']
    if city != 'любой':
        rm = data_filter_user(rm, 5, city)

    rm = provider_filter(rm, data['save_user'].split(','))

    vostok_client = data['messager']
    if vostok_client in ['да', 'нет']:
        r = data_filter_user(rm, 7, 'восток')
        if vostok_client == 'да':
            rm = r
        else:
            rm = [i for i in rm if i not in r]  # убираем все вхождения строк у которых нет востока

    whatsApp = data['number_operator']
    if whatsApp in ['да', 'нет']:
        r = data_filter_user(rm, 8, 'ватсап')
        if whatsApp == 'да':
            rm = r
        else:
            rm = [i for i in rm if i not in r]

    rm = rm[:data['count_users']]
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    for row in rm:
        worksheet.append(row)
    workbook.save(filename=data['filename'])

    with open(outfile_filename, "a", encoding="utf-8") as file:
        writer = csv.writer(file)
        for row in rm:
            writer.writerow(row)

    # remove `rm` data from `data_filename`
    with open(data_filename, 'r') as inp, open(data_filename+".changed", 'w') as out:
        writer = csv.writer(out)
        for row in csv.reader(inp):
            if row[0].split(";") not in rm:
                writer.writerow(row)
    os.remove(data_filename)
    os.rename(data_filename+".changed", data_filename)

    await message.answer_document(document=types.InputFile(data['filename']))  # 0:int(message.text) так как это последнее состояние
    os.remove(data['filename'])
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


@dp.message_handler(commands=["info"])
async def process_info(message: types.Message):
    await message.answer("Подождите, идет обработка данных...")
    data = list()
    with open(data_filename, newline='', encoding='utf-8') as csvfile:
        csv_data = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in csv_data:
            data.append(row)

    availiable_whatsapp = len([i for i in data if i[8] == "ватсап"])
    not_availiable_whatsapp = len([i for i in data if i[8] != "ватсап"])

    availiable_v = len([i for i in data if i[7] == "восток"])
    not_availiable_v = len([i for i in data if i[7] != "восток"])


    availiable_towns = set([i[5] for i in data]) # список городов
    # убираем "" из сета
    while "" in availiable_towns:
        availiable_towns.remove("")
    result_towns = dict()
    for town in availiable_towns:
        result_towns[town] = len([i for i in data if i[5] == town])
    string_result_towns = "\n".join([f"{town}: {count}" for town, count in result_towns.items()])

    availiable_ops = set([i[4] for i in data]) # список городов
    # убираем "" из сета
    while "" in availiable_ops:
        availiable_ops.remove("")
    result_ops = dict()
    for op in availiable_ops:
        result_ops[op] = len([i for i in data if i[4] == op])
    string_result_ops = "\n".join([f"{op}: {count}" for op, count in result_ops.items()])

    await message.answer("Всего данных:\n"
                         f"<b>восток:</b> {availiable_v}\n"
                         f"<b>не восток:</b> {not_availiable_v}\n"
                         f"<b>ватсап:</b> {availiable_whatsapp}\n"
                         f"<b>не ватсап:</b> {not_availiable_whatsapp}\n"
                         "<b>По регионам</b>\n"
                         f"{string_result_towns}"
                         f"\n<b>По операторам</b>\n"
                         f"{string_result_ops}",
                         parse_mode="HTML"
                         )


if __name__ == '__main__':
    executor.start_polling(dp)


