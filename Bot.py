from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text, state
from aiogram.utils.exceptions import MessageNotModified
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import ConnectDB  # Созданный модуль для работы с PostgreSQL
import os
import logging
import math
import sys


logging.basicConfig(filename='bot.log', level=logging.INFO, format='[%(asctime)s: %(levelname)s] %(message)s')

BASE_URL = 'codeforces.com'
bot_token = os.getenv('BOT_TOKEN')
if not bot_token:
    logging.critical('bot::not token not available')
    sys.exit('bot token not available')

storage = MemoryStorage()
bot = Bot(token=bot_token)
dp = Dispatcher(bot, storage=storage)

USER_DATA = {}  # Контейнер для поиска сета задач


class FormSingleSearch(state.StatesGroup):
    """Форма для поиска одного задания"""
    name = state.State()
    rank = state.State()
    notice = state.State()


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """
    Приветственный хендлер
    :param message: Объект сообщения
    :return:
    """
    USER_DATA.clear()
    start_keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text='Выбрать набор задач'), types.KeyboardButton(text='Искать задачу')]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    text = 'Давай найдём что порешать! 🚀'
    await message.answer(text, reply_markup=start_keyboard)


@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    """
    Хендлер выводящий спасательную информацию о боте
    :param message: Объект сообщения
    :return:
    """
    await message.answer('Я могу помочь выбрать задачи с Codeforces!\n'
                         'Для начала введи команду /start или открой клавиатуру ☺')


@dp.message_handler(Text(contains='Искать задачу'))
async def cmd_get_single(message: types.Message, state: FSMContext):
    """
    Хендлер для поиска определенной задачи из БД
    :param state: Объект для работы с машиной состояний
    :param message: Объект сообщения
    :return:
    """
    single_keyboard = types.ReplyKeyboardMarkup(
        [
            [types.KeyboardButton('Указать название')],
            [types.KeyboardButton('Указать сложность'), types.KeyboardButton('Указать категорию')],
            [types.KeyboardButton('Отменить поиск'), types.KeyboardButton('Поиск')]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    data = await state.get_data()
    text = f"Имя: {data['name'] if 'name' in data else ''}\n" \
           f"Сложность: {data['rank'] if 'rank' in data else ''}\n" \
           f"Категория: {data['notice'] if 'notice' in data else ''}\n"
    await message.answer(text, reply_markup=single_keyboard)


@dp.message_handler(Text(contains='Указать название'))
async def cmd_single_name(message: types.Message):
    """
    Хендлер для запроса указания названия искомой задачи
    :param message: Объект сообщения
    :return:
    """
    await message.answer('Введите название задачи')
    await FormSingleSearch.name.set()


@dp.message_handler(state=FormSingleSearch.name)
async def set_single_name(message: types.Message, state: FSMContext):
    """
    Хендлер для сохранения названия искомой задачи
    :param message: Объект сообщения
    :param state: Объект для работы с машиной состояний
    :return:
    """
    await state.update_data(name=message.text)
    await state.reset_state(with_data=False)
    await message.answer('Отлично! Название записано!')
    await cmd_get_single(message, state)


@dp.message_handler(Text(contains='Указать сложность'))
async def cmd_single_rank(message: types.Message):
    """
    Хендлер для запроса указания сложности искомой задачи
    :param message: Объект сообщения
    :return:
    """
    await message.answer('Введите сложность задачи')
    await FormSingleSearch.rank.set()


@dp.message_handler(state=FormSingleSearch.rank)
async def set_single_rank(message: types.Message, state: FSMContext):
    """
    Хендлер для сохранения сложности искомой задачи
    :param message: Объект сообщения
    :param state: Объект для работы с машиной состояний
    :return:
    """
    await state.update_data(rank=message.text)
    await state.reset_state(with_data=False)
    await message.answer('Отлично! Сложность записана!')
    await cmd_get_single(message, state)


@dp.message_handler(Text(contains='Указать категорию'))
async def cmd_single_notice(message: types.Message):
    """
    Хендлер для запроса указания категории искомой задачи
    :param message: Объект сообщения
    :return:
    """
    await message.answer('Введите категорию задачи')
    await FormSingleSearch.notice.set()


@dp.message_handler(state=FormSingleSearch.notice)
async def set_single_notice(message: types.Message, state: FSMContext):
    """
    Хендлер для сохранения категории искомой задачи
    :param message: Объект сообщения
    :param state: Объект для работы с машиной состояний
    :return:
    """
    await state.update_data(notice=message.text)
    await state.reset_state(with_data=False)
    await message.answer('Отлично! Категория записана!')
    await cmd_get_single(message, state)


@dp.message_handler(Text(contains='Отменить поиск'))
async def cmd_single_cancel(message: types.Message, state: FSMContext):
    """
    Хендлер для отмены поиска задачи
    :param state: Объект для работы с машиной состояний
    :param message: Объект сообщения
    :return:
    """
    await message.answer('Поиск остановлен 🤫')
    await state.finish()
    await cmd_start(message)


@dp.message_handler(Text(contains='Поиск'))
async def cmd_single_search(message: types.Message, state: FSMContext):
    """
    Хендлер для поиска задачи
    :param state: Объект для работы с машиной состояний
    :param message: Объект сообщения
    :return:
    """
    data = await state.get_data()
    if 'name' not in data and 'rank' not in data and 'notice' not in data:
        await message.answer('Не указаны данные для поиска 🤔')
        await cmd_get_single(message, state)
    elif 'name' not in data:
        await _single_not_have_name_in_data(message, state, data)
    else:
        await _single_have_name_in_data(message, state, data)


async def _single_not_have_name_in_data(message: types.Message, state: FSMContext, data: dict):
    """
    Функция для обработки различных состояний запроса на поиск определенного задания
    при отсутствии указанного названия задачи
    :param state: Объект для работы с машиной состояний
    :param message: Объект сообщения
    :param data: Словарь с данными
    :return:
    """
    db = ConnectDB.ConDB()
    if 'rank' not in data:
        query = """
        SELECT name, rank, link
        FROM codeforces INNER JOIN notice_query USING(id_codeforces)
        INNER JOIN notice USING(id_notice)
        WHERE notice_name=%s
        """
        vars = (data['notice'],)
        task_list = db.select(query, vars)
        if len(task_list) == 0:
            await _single_not_found(message, state)
        elif len(task_list) < 20:
            await _single_print_keyboard(message, state, task_list)
        else:
            query = """
            SELECT rank
            FROM codeforces INNER JOIN notice_query USING(id_codeforces)
            INNER JOIN notice USING(id_notice)
            WHERE notice_name=%s
            GROUP BY rank
            """
            rank_list = sorted(str(i[0]) for i in db.select(query, vars) if i[0])
            text = f"Результат слишком большой 😓\nУкажите дополнительные параметры поиска!\n" \
                   f"Список доступных сложностей в данной категории в помощь 😇\n{', '.join(rank_list)}"
            await message.answer(text)
            await cmd_get_single(message, state)
    elif 'notice' not in data:
        query = """
        SELECT name, rank, link
        FROM codeforces INNER JOIN notice_query USING(id_codeforces)
        INNER JOIN notice USING(id_notice)
        WHERE rank=%s
        """
        vars = (data['rank'],)
        task_list = db.select(query, vars)
        if len(task_list) == 0:
            await _single_not_found(message, state)
        elif len(task_list) < 20:
            await _single_print_keyboard(message, state, task_list)
        else:
            query = """
            SELECT notice_name
            FROM codeforces INNER JOIN notice_query USING(id_codeforces)
            INNER JOIN notice USING(id_notice)
            WHERE rank=%s
            GROUP BY notice_name
            """
            rank_list = sorted(i[0] for i in db.select(query, vars) if i[0])
            text = f"Результат слишком большой 😓\nУкажите дополнительные параметры поиска!\n" \
                   f"Список доступных категорий при заданной сложности в помощь 😇\n{', '.join(rank_list)}"
            await message.answer(text)
            await cmd_get_single(message, state)
    else:
        query = """
        SELECT name, rank, link
        FROM codeforces INNER JOIN notice_query USING(id_codeforces)
        INNER JOIN notice USING(id_notice)
        WHERE notice_name=%s AND rank=%s
        """
        vars = (data['notice'], data['rank'])
        task_list = db.select(query, vars)
        if len(task_list) == 0:
            await _single_not_found(message, state)
        else:
            await _single_print_keyboard(message, state, task_list)


async def _single_have_name_in_data(message: types.Message, state: FSMContext, data: dict):
    """
    Функция для обработки различных состояний запроса на поиск определенного задания
    при наличии указанного названия задачи
    :param state: Объект для работы с машиной состояний
    :param message: Объект сообщения
    :param data: Словарь с данными
    :return:
    """
    db = ConnectDB.ConDB()
    name = data['name']
    if 'rank' not in data and 'notice' not in data:
        query = """
        SELECT name, rank, link
        FROM codeforces INNER JOIN notice_query USING(id_codeforces)
        INNER JOIN notice USING(id_notice)
        WHERE name LIKE %s
        GROUP BY name, rank, link
        """
        vars = ('%' + name + '%',)
    elif 'rank' not in data:
        query = """
        SELECT name, rank, link
        FROM codeforces INNER JOIN notice_query USING(id_codeforces)
        INNER JOIN notice USING(id_notice)
        WHERE name LIKE %s AND notice_name LIKE %s
        """
        vars = ('%' + name + '%', '%' + data['notice'] + '%')
    elif 'notice' not in data:
        query = """
        SELECT name, rank, link
        FROM codeforces INNER JOIN notice_query USING(id_codeforces)
        INNER JOIN notice USING(id_notice)
        WHERE name LIKE %s AND rank=%s
        GROUP BY name, rank, link
        """
        vars = ('%' + name + '%', data['rank'])
    else:
        query = """
        SELECT name, rank, link
        FROM codeforces INNER JOIN notice_query USING(id_codeforces)
        INNER JOIN notice USING(id_notice)
        WHERE name LIKE %s AND notice_name LIKE %s AND rank=%s
        """
        vars = ('%' + name + '%', '%' + data['notice'] + '%', data['rank'])
    task_list = db.select(query, vars)
    if len(task_list) == 0:
        await _single_not_found(message, state)
    else:
        await _single_print_keyboard(message, state, task_list)


async def _single_not_found(message: types.Message, state: FSMContext):
    """
    Вспомогательная функция для действий при остутствии результатов поиска
    :param state: Объект для работы с машиной состояний
    :param message: Объект сообщения
    :return:
    """
    text = 'Не удалось найти задачи 😯'
    await message.answer(text)
    await cmd_get_single(message, state)


async def _single_print_keyboard(message: types.Message, state: FSMContext, mapping: list):
    """
    Вспомогательная функция для формирования клавиатуры и её вывода
    :param state: Объект для работы с машиной состояний
    :param message: Объект сообщения
    :param mapping: Итерируемая последовательность
    :return:
    """
    keyboard = types.InlineKeyboardMarkup()
    for task in mapping:
        keyboard.add(types.InlineKeyboardButton(task[0] + ' Сложность: ' + str(task[1]), url=BASE_URL + task[2]))
    text = 'Найдено по запросу 😎'
    await message.answer(text, reply_markup=keyboard)


@dp.message_handler(Text(contains='Выбрать набор задач'))
async def cmd_get_set(message: types.Message):
    """
    Хендлер позволяющий выбрать набор задач по сложности и категории из БД
    :param message: Объект сообщения
    :return:
    """
    db = ConnectDB.ConDB()

    rank_keyboard = types.InlineKeyboardMarkup()
    for i in _get_ranks(db):
        rank_keyboard.add(types.InlineKeyboardButton(text=i, callback_data=f'set_rank_{i}'))
    await message.answer('Выберите необходимую сложность задачи', reply_markup=rank_keyboard)


@dp.callback_query_handler(Text(startswith='set_'))
async def callback_get_set(callback: types.CallbackQuery):
    """
    Хендлер организующий обмен информацией с пользователем для вывода нужного набора задач из БД
    :param callback: внутренний запрос с данными от пользователя
    :return:
    """
    action = callback['data'].split('set_', 1)[1]

    if action.startswith('rank'):
        await _get_set_rank(callback, action)
    elif action.startswith('num_'):
        await _get_set_num(callback, action)
    elif action.startswith('n'):
        await _get_set_notice(callback, action)

    await callback.answer()


async def _get_set_rank(callback: types.callback_query, action: str) -> None:
    """
    Обработка сложности задачи из запроса и формирование клавиатуры с категориями задач
    :param callback: обратный запрос
    :param action: строка с сложностью задачи из запроса
    :return:
    """
    db = ConnectDB.ConDB()

    rank = int(action.split('rank_', 1)[1])
    USER_DATA['rank'] = rank

    notice_keyboard = types.InlineKeyboardMarkup()
    for notice in _get_notices(db, rank):
        notice_keyboard.add(types.InlineKeyboardButton(text=_validate_len_str(notice), callback_data=f'set_n_{notice}'))
    await _update_markup(callback.message, 'Выберите необходимую категорию', notice_keyboard)


async def _get_set_notice(callback: types.callback_query, action: str) -> None:
    """
    Обработка категории задач и формирование клавиатуры с выбором сета задач
    :param callback: обратный запрос
    :param action: запрос с категорией задач
    :return:
    """
    db = ConnectDB.ConDB()

    notice = action.split('n_', 1)[1]
    USER_DATA['notice'] = notice
    if 'rank' in USER_DATA:
        USER_DATA['data'] = _get_all_sets(db, USER_DATA['rank'], notice)

        num_keyboard = types.InlineKeyboardMarkup()
        count_set = math.ceil(len(USER_DATA['data']) / 10)
        for i in range(1, count_set + 1):
            num_keyboard.add(types.InlineKeyboardButton(text=f'Набор № {i}', callback_data=f'set_num_{i}'))
        await _update_markup(callback.message, 'Выберите номер набора', num_keyboard)
    else:
        logging.error('Bot::_get_set_notice::отсутствует сложность задачи перед поиском категории задачи')
        await callback.message.delete()
        await callback.message.answer("Что-то пошло не так! Предлагаю начать сначала 😉")
        await cmd_start(callback.message)


async def _get_set_num(callback: types.callback_query, action: str) -> None:
    """
    Обработка вывода конкретного набора задач и вывод клавиатуры с списком этих задач
    :param callback: обратный запрос
    :param action: запрос с номером сета задач
    :return:
    """
    if 'rank' in USER_DATA and 'notice' in USER_DATA and 'data' in USER_DATA:
        num = int(action.split('num_', 1)[1])

        data = USER_DATA['data']
        start_ind = (num - 1) * 10
        end_ind = min(len(data), start_ind + 10)
        result_set = data[start_ind: end_ind]

        set_keyboard = types.InlineKeyboardMarkup()
        for task in result_set:
            name = task[0]
            url = BASE_URL + task[1]
            set_keyboard.add(types.InlineKeyboardButton(text=_validate_len_str(name), url=url))
        await _update_markup(callback.message, f'Набор № {num}', set_keyboard)
    else:
        logging.error('Bot::_get_set_num::нарушен порядок заполнения данных для поиска в БД')
        await callback.message.delete()
        await callback.message.answer("Что-то пошло не так! Предлагаю начать сначала 😉")
        await cmd_start(callback.message)


async def _update_markup(message: types.Message, text: str, markup: types.InlineKeyboardMarkup) -> None:
    """
    Вспомогательная функция для изменения инлайн клавиатуры
    :param message: Сообщение, в котором будут происходить изменения
    :param text: Текст перед клавиатурой, на который будет произведена замена
    :param markup: Новая клавиатура
    :return:
    """
    print(markup)
    try:
        await message.edit_text(text)
        await message.edit_reply_markup(reply_markup=markup)
    except MessageNotModified as e:
        logging.error(f'Bot::_update_markup::{e}')
        await message.delete()
        await message.answer("Что-то пошло не так! Предлагаю начать сначала 😉")
        await cmd_start(message)


def _get_ranks(db: ConnectDB.ConDB) -> list:
    """
    Поиск в БД сложности задач
    :param db: Объект работающий с PostgreSQL
    :return: Отсортированный список возможных сложностей в задачах
    """
    query = """
    SELECT rank
    FROM codeforces INNER JOIN notice_query USING(id_codeforces)
    INNER JOIN notice USING(id_notice)
    GROUP BY rank
    """
    return sorted((i[0] for i in db.select(query) if i[0]))


def _get_notices(db: ConnectDB.ConDB, rank: int) -> list:
    """
    Поиск в БД категорий задач по их сложности
    :param db: Объект работающий с PostgreSQL
    :param rank: Сложность задачи
    :return: Отсортированный список из категорий задач
    """
    query = """
    SELECT notice_name
    FROM codeforces INNER JOIN notice_query USING(id_codeforces)
    INNER JOIN notice USING(id_notice)
    WHERE rank=%s
    GROUP BY notice_name
    """
    vars = (rank,)
    return sorted((i[0] for i in db.select(query, vars) if i[0]))


def _get_all_sets(db: ConnectDB.ConDB, rank: int, notice: str) -> list:
    """
    Осуществляет поиск в БД по сложности и категории задачи
    :param db: Объект работающий с PostgreSQL
    :param rank: Сложность задачи
    :param notice: Категория задачи
    :return: Список с именами и ссылками из искомых данных
    """
    query = """
    SELECT name, link
    FROM codeforces INNER JOIN notice_query USING(id_codeforces)
    INNER JOIN notice USING(id_notice)
    WHERE rank=%s AND notice_name=%s
    """
    vars = (rank, notice)
    return db.select(query, vars)


def _validate_len_str(value: str) -> str:
    """
    Ограничение длины слова до 21 символа для инлайн кнопок
    :param value: Слово для ограничения
    :return: Ограниченное слово
    """
    if len(value) > 20:
        value = value[:18] + '..'
    return value


if __name__ == '__main__':
    executor.start_polling(dp)
