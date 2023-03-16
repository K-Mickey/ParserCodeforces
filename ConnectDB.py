import logging
import psycopg2
import os
from singleton_decorator import singleton


@singleton
class ConDB:
    """
    Объект для организованного взаимодействия с PostgreSQL
    """
    def __init__(self):
        """
        Соединение с БД и создание таблиц при необходимости
        """
        self.__insert_count = -1  # Равно -1, так как через метод insert происходит проверка созданы ли таблицы

        self.__conn = psycopg2.connect(
            database=os.getenv('DATABASE_NAME'),
            user=os.getenv('DATABASE_USER'),
            password=os.getenv('DATABASE_PASSWORD'),
            host=os.getenv('DATABASE_HOST'),
            port=os.getenv('DATABASE_PORT'),
        )
        logging.info('ConDB::Database Connected...')
        self._create_tables()

    def __del__(self):
        """
        Сохранение изменений и закрытие соединения с БД
        :return:
        """
        self.__conn.close()
        logging.info('ConDB::Database close')

    def select(self, query: str, vars: tuple = None) -> list:
        """
        Выборка данных из БД
        :param query: PostgreSQL запрос
        :param vars: Последовательность атрибутов для формирования запроса
        :return: список данных
        """
        cur = self.__conn.cursor()
        cur.execute(query, vars)
        res = cur.fetchall()
        cur.close()
        return res

    def insert(self, query: str, vars: tuple = None) -> None:
        """
        Добавление данных в БД
        :param query: PostgreSQL запрос
        :param vars: Последовательность атрибутов для формирования запроса
        :return: None
        """
        cur = self.__conn.cursor()
        cur.execute(query, vars)
        self.__conn.commit()
        cur.close()
        self.__insert_count += 1

    def get_insert_count(self):
        return self.__insert_count

    def _create_tables(self):
        query = """
        CREATE TABLE IF NOT EXISTS codeforces(
        id_codeforces SERIAL PRIMARY KEY, 
        name VARCHAR, 
        rank INTEGER, 
        count_solve INTEGER,
        link VARCHAR);
        CREATE TABLE IF NOT EXISTS notice(
        id_notice SERIAL PRIMARY KEY, 
        notice_name VARCHAR);
        CREATE TABLE IF NOT EXISTS notice_query(
        id_notice_query BIGSERIAL PRIMARY KEY,
        id_codeforces INTEGER NOT NULL REFERENCES codeforces, 
        id_notice INTEGER NOT NULL REFERENCES notice,
        UNIQUE (id_codeforces, id_notice));
        """
        self.insert(query)  # Алгоритм insert такой же, как и при создании таблицы


def update_database_codeforces(db: ConDB, name: str, rank: int, count_solve: int, notice_lst: list, link: str) -> None:
    """
    Обновление БД данными из таблицы с сайта Codeforces
    :param db: Объект работающий с PostgreSQL
    :param name: имя добавляемой задачи
    :param rank: rank добавляемой задачи
    :param count_solve: количество решений добавляемой задачи
    :param notice_lst: список категорий добавляемой задачи
    :param link: ссылка на добавляемую задачу
    :return: None
    """
    if _update_codeforces(db, name, rank, count_solve, link):
        id_codeforces = _get_codeforces_id(db)
        for notice_name in notice_lst:
            id_notice = _get_notice_id(db, notice_name)
            _add_notice_query(db, id_codeforces, id_notice)


def _update_codeforces(db: ConDB, name: str, rank: int, count_solve: int, link: str) -> bool:
    """
    Вспомогательная функция по осуществлению запроса insert к таблице codeforces при отсутствии таких же данных в ней
    :param db: Объект работающий с PostgreSQL
    :param name: имя добавляемой задачи
    :param rank: rank добавляемой задачи
    :param count_solve: количество решений добавляемой задачи
    :param link: ссылка на добавляемую задачу
    :return: True, если произведена запись в БД, False в противном случае
    """
    query = "SELECT name FROM codeforces WHERE codeforces.name=%s;"
    vars = (name, )
    if not db.select(query, vars):
        query = "INSERT INTO codeforces(name, rank, count_solve, link) VALUES(%s, %s, %s, %s);"
        vars = (name, rank, count_solve, link)
        db.insert(query, vars)
        return True
    return False


def _get_codeforces_id(db: ConDB) -> int:
    """
    Вспомогательная функция по осуществлению запроса select к таблице codeforces и возврату id найденных данных
    :param db: Объект работающий с PostgreSQL
    :return: id последнего добавленного элемента таблицы
    """
    query = "SELECT id_codeforces FROM codeforces ORDER BY id_codeforces DESC LIMIT 1;"
    return db.select(query)[0][0]


def _get_notice_id(db: ConDB, notice_name: str) -> int:
    """
    Вспомогательная функция на осуществление запроса insert к таблице notice и возврату id добавленных данных
    :param db: Объект работающий с PostgreSQL
    :param notice_name: Имя, которое будет добавлено в таблицу
    :return: id элемента с именем notice_name в таблице notice
    """
    query_select = "SELECT id_notice FROM notice WHERE notice_name=%s;"
    vars = (notice_name, )
    id_notice = db.select(query_select, vars)
    if not id_notice:
        query_insert = "INSERT INTO notice(notice_name) VALUES(%s);"
        db.insert(query_insert, vars)
        id_notice = db.select(query_select, (notice_name, ))
    return id_notice[0][0]


def _add_notice_query(db: ConDB, id_codeforces: int, id_notice: int) -> None:
    """
    Вспомогательная функция по осуществлению запроса insert к таблице notice_query,
    определяющей взаимосвязь таблиц notice и codeforces
    :param db: Объект работающий с PostgreSQL
    :param id_codeforces: id элемента из таблицы codeforces
    :param id_notice: id элемента из таблицы notice
    :return: None
    """
    query = "SELECT * FROM notice_query WHERE id_codeforces=%s AND id_notice=%s;"
    vars = (id_codeforces, id_notice)
    if not db.select(query, vars):
        query = "INSERT INTO notice_query(id_codeforces, id_notice) VALUES(%s, %s);"
        db.insert(query, vars)
