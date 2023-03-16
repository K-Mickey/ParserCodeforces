from bs4 import BeautifulSoup
import bs4
import requests
import logging
import time
import tqdm
import ConnectDB  # Созданный модуль


logging.basicConfig(filename='parser.log', level=logging.INFO, format='[%(asctime)s: %(levelname)s] %(message)s')

BASE_URL = 'https://codeforces.com'
POSTFIX_URL = '?order=BY_SOLVED_DESC&locale=ru'
URL = f'{BASE_URL}/problemset{POSTFIX_URL}'
SLEEP_MINUTE = 60


def dispatcher():
    """
    Организация работы парсера сайта Codeforces
    :return:
    """
    print("Hello, I'm running!")
    logging.info(f"parser::{'-' * 10}Start program...{'-' * 10}")
    try:
        while True:
            parse_site()
            logging.info(f'parser::Parser start sleep...')
            for _ in tqdm.trange(SLEEP_MINUTE, desc='Minutes to next run'):
                time.sleep(60)
            logging.info(f'parser::Parser wakes up...')
    except KeyboardInterrupt:
        pass
    finally:
        logging.info(f"parser::{'-' * 10}The end!{'-' * 10}")
        logging.info('')
        print("Bye, bye! I'm done!")


def parse_site():
    """
    Организация парсинга сайта
    database: объект БД
    bs: код страницы
    parse_page: парсинг страницы и добавление в БД
    find_next_page: поиск ссылки на следующую страницу
    :return:
    """
    database = ConnectDB.ConDB()
    cur_url = URL
    count_page = 0
    logging.info('parser::The parser started working with the site')
    try:
        while True:
            count_page += 1
            logging.debug(f'Parsing {count_page} page.')

            r = requests.get(url=cur_url)
            if not r.raise_for_status():
                bs = BeautifulSoup(r.text, 'lxml')
                table = bs.find_all('tr')

                parse_page(database, table)

                try:
                    cur_url = find_next_page(bs)
                except AttributeError:
                    logging.info(f'parser::Page {count_page} last. Except AttributeError.')
                    logging.info(f'parser::The number of records added to the database = {database.get_insert_count()}')
                    break
    except KeyboardInterrupt:
        logging.info(f'parser::User pressed stop. The number of records added to the database = {database.get_insert_count()}')


def find_next_page(page: BeautifulSoup) -> str:
    """
    Поиск и формирование ссылки на следующую страницу
    :param page: объект BeatifulSoup
    :return: ссылка на следующую страницу
    """
    paginator = page.find('div', class_='pagination')
    cur_page = paginator.find('span', class_='page-index active')
    next_page = cur_page.find_next('span', class_='page-index').find('a')
    return f"{BASE_URL}/{next_page.attrs['href']}&locale=ru"


def parse_page(db: ConnectDB.ConDB, table: BeautifulSoup) -> None:
    """
    Парсинг таблицы на странице сайта и добавление данных в БД
    :param db: объект для работа с PostgreSQL
    :param table: объект BeautifulSoup
    :return:
    """
    for i, v in enumerate(table):
        string = table[i]

        if not string.find('th'):
            ConnectDB.update_database_codeforces(
                db,
                parse_name(string) + ' - ' + parse_number(string),
                parse_rank(string),
                parse_count_solve(string),
                parse_notice(string),
                parse_link(string),
            )


def parse_number(string: bs4.BeautifulSoup) -> str:
    """
    Поиск номера задачи в строке таблицы
    :param string: строка таблицы
    :return: номер задачи в str
    """
    try:
        number = string.find('td', class_='id').text.strip()
    except AttributeError as e:
        logging.error(f'parse_number: {e}')
        number = None
    return number


def parse_name(string: bs4.BeautifulSoup) -> str:
    """
    Поиск имени задачи в строке таблицы
    :param string: строка таблицы
    :return: имя задачи в str
    """
    try:
        name = string.find('div', style='float: left;').text.strip()
    except AttributeError as e:
        logging.error(f'parse_name: {e}')
        name = None
    return name


def parse_notice(string: bs4.BeautifulSoup) -> list:
    """
    Поиск тематик задач
    :param string: строка таблицы
    :return: список тематик задачи
    """
    try:
        notice = [i.text.strip() for i in string.find_all('a', class_='notice')]
    except AttributeError as e:
        logging.error(f'parse_notice {e}')
        notice = None
    return notice


def parse_rank(string: bs4.BeautifulSoup) -> int:
    """
    Поиск сложности задачи
    :param string:  строка таблицы
    :return: Сложность задачи в int
    """
    try:
        rank = string.find('span', class_='ProblemRating')
        if rank:
            rank = int(rank.text.strip())
    except (AttributeError, ValueError) as e:
        logging.error(f'parse_rank: {e}')
        rank = None
    return rank


def parse_count_solve(string: bs4.BeautifulSoup) -> int:
    """
    Поиск количества решений задачи
    :param string: строка таблицы
    :return: количество решений в int
    """
    try:
        count_solve = string.find('a', title='Participants solved the problem')
        if count_solve:
            count_solve = int(count_solve.text.strip()[1:])
    except (AttributeError, IndexError, ValueError) as e:
        logging.error(f'parse_count_solve {e}')
        count_solve = None
    return count_solve


def parse_link(string: bs4.BeautifulSoup) -> str:
    """
    Поиск ссылки на задачу
    :param string: строка таблицы
    :return: количество решений в int
    """
    try:
        link = string.find('a').get('href')
    except AttributeError as e:
        logging.error(f'parse_count_solve {e}')
        link = None
    return link


if __name__ == '__main__':
    dispatcher()
