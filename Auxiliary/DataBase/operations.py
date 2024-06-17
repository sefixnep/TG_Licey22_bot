import json
import sqlite3

from time import sleep
from datetime import datetime, timedelta
from math import ceil

from Auxiliary.chat import *

contests = {'past': list(), 'present': list(), 'future': list()}


class Paths:
    DataBase = 'DataBase.db'


def creating_tables():
    # Подключение к базе данных
    connection = sqlite3.connect(Paths.DataBase)
    cursor = connection.cursor()

    # Создание таблицы "contests", если она не существует
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS "contests" (
      "id" INTEGER PRIMARY KEY AUTOINCREMENT,
      "name" VARCHAR(255) NOT NULL,
      "date_start" DATETIME NOT NULL,
      "date_end" DATETIME NOT NULL,
      "tags" JSON NOT NULL,
      "comment" TEXT
    );
    """)

    # Создание таблицы "statuses", если она не существует
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS "statuses" (
        "id" INTEGER NOT NULL PRIMARY KEY UNIQUE,
        "status" TEXT NOT NULL
    );
    """)

    # Сохранение изменений
    connection.commit()

    # Закрытие соединения
    connection.close()


# Contests
def get_contest(id):
    # Подключение к базе данных
    connection = sqlite3.connect(Paths.DataBase)
    cursor = connection.cursor()

    # Находим нужный конкурс по id
    cursor.execute("SELECT * FROM contests WHERE id = ?", (id,))

    # Достаем данные из таблицы и преобразуем теги
    contest = cursor.fetchone()
    contest = (contest[:config.contest_indices.index('tags')] +
               (json.loads(contest[config.contest_indices.index('tags')]),) +
               contest[config.contest_indices.index('tags') + 1:])

    # Закрытие соединения
    connection.close()

    return contest


def record_contest(name: str, date_start: str, date_end: str, tags: list, comment=None):
    # Преобразование данных в формат, подходящий для SQLite
    # Тут должно быть преобразование любого формата даты в строку вида .strftime('%Y-%m-%d')
    tags = json.dumps(tags)

    # Подключение к базе данных
    connection = sqlite3.connect(Paths.DataBase)
    cursor = connection.cursor()

    # Ищем такой-же конкурс
    cursor.execute("SELECT id FROM contests WHERE "
                   "name = ? AND "
                   "date_start = ? AND "
                   "date_end = ?", (name, date_start, date_end))

    # Запись данных в таблицу contests если такого конкурса не было
    if cursor.fetchone() is None:
        cursor.execute("""
            INSERT INTO "contests" (
              "name",
              "date_start",
              "date_end",
              "tags",
              "comment"
            )
            VALUES (?, ?, ?, ?, ?)
            """, (name, date_start, date_end, tags, comment))

        # Сохранение изменений
        connection.commit()

    # Закрытие соединения
    connection.close()


def remove_old_contests():
    # Подключение к базе данных
    connection = sqlite3.connect(Paths.DataBase)
    cursor = connection.cursor()

    # Определение текущей даты и даты, от config.removal_day дней назад
    current_date = datetime.now()
    thirty_days_ago = current_date - timedelta(days=config.removal_day)

    # Преобразование дат в формат, подходящий для SQLite
    thirty_days_ago_str = thirty_days_ago.strftime('%Y-%m-%d')

    # Выполнение запроса к базе данных
    cursor.execute("""
    DELETE FROM contests 
    WHERE date_end < ?;
""", (thirty_days_ago_str,))

    # Сохранение изменений
    connection.commit()

    # Закрытие соединения
    connection.close()


def contests_filter_tense(tense):
    # Подключение к базе данных
    connection = sqlite3.connect(Paths.DataBase)
    cursor = connection.cursor()

    # Создание запроса
    query = None

    if tense == 'all':
        query = "SELECT * FROM contests"
    elif tense == 'past':
        query = "SELECT * FROM contests WHERE date_end < CURRENT_TIMESTAMP"
    elif tense == 'present':
        query = "SELECT * FROM contests WHERE date_start < CURRENT_TIMESTAMP AND CURRENT_TIMESTAMP < date_end"
    elif tense == 'future':
        query = "SELECT * FROM contests WHERE CURRENT_TIMESTAMP < date_start"

    assert query is not None, "tense must be past/present/future"

    # Выполнение запроса и получение результатов
    cursor.execute(query)
    records = cursor.fetchall()

    for i in range(len(records)):
        records[i] = (records[i][:config.contest_indices.index('tags')] +
                      (json.loads(records[i][config.contest_indices.index('tags')]),) +
                      records[i][config.contest_indices.index('tags') + 1:])

    # Закрытие соединения с базой данных
    connection.close()

    return records


def update(lst: list, tense):
    lst.clear()
    contests_tense = contests_filter_tense(tense)
    amount_pages = ceil(len(contests_tense) / (config.shape[0] * config.shape[1]))

    def leafing(count):
        if amount_pages == 1:
            return ((button.back_to_contests_tense,),)
        elif amount_pages > 1 and count == 0:
            return ((button.back_to_contests_tense,
                     Button(" >> ", f"right_{tense}_{count + 1}_contests")),)
        elif amount_pages > 1 and count == amount_pages - 1:
            return ((Button(" << ", f"left_{tense}_{count - 1}_contests"),
                     button.back_to_contests_tense,),)
        else:
            return ((Button(" << ", f"left_{tense}_{count - 1}_contests"),
                     button.back_to_contests_tense,
                     Button(" >> ", f"right_{tense}_{count + 1}_contests")),)

    for i in range(amount_pages):
        Button("🔙 Назад 🔙", f'back_to_{tense}_{len(lst)}_contests')
        page = tuple()
        for j in range(config.shape[0]):
            line = tuple()
            for n in range(config.shape[1]):
                if len(contests_tense) == i * config.shape[0] * config.shape[1] + j * config.shape[1] + n:
                    if j + n:
                        if n:
                            page += (line,)
                        page += leafing(i)
                        lst.append(page)
                    return None

                contest = contests_tense[i * config.shape[0] * config.shape[1] + j * config.shape[1] + n]
                callback_data = f'{contest[config.contest_indices.index("id")]}_contest'

                Button(contest[config.contest_indices.index('name')], callback_data)
                Message(' '.join(map(str, contest)), ((getattr(button, f'back_to_{tense}_{len(lst)}_contests'),),),
                        getattr(button, callback_data))

                line += (getattr(button, callback_data),)
            page += (line,)

        page += leafing(i)
        lst.append(page)


# Statuses
def get_status(chat_id: str):
    # Подключение к базе данных
    connection = sqlite3.connect(Paths.DataBase)
    cursor = connection.cursor()

    # Находим нужный статус по chat_id
    cursor.execute("SELECT status FROM statuses WHERE id = ?", (chat_id,))

    status = cursor.fetchone()

    # Закрытие соединения
    connection.close()

    return status[0] if status is not None else None


def assign_status(chat_id: str, status: str):
    # Подключение к базе данных
    connection = sqlite3.connect(Paths.DataBase)
    cursor = connection.cursor()

    # Получим нынешний статус
    temp = get_status(chat_id)

    # Запись данных в таблицу statuses
    if temp is None and status:
        cursor.execute("""
        INSERT INTO "statuses" (
          "id",
          "status"
        )
        VALUES (?, ?)
        """, (chat_id, status))
    elif temp is not None and status:
        cursor.execute("UPDATE statuses SET status = ? WHERE id = ?", (status, chat_id))
    elif temp is not None and not status:
        cursor.execute("DELETE FROM statuses WHERE id = ?", (chat_id,))

    # Сохранение изменений
    connection.commit()

    # Закрытие соединения
    connection.close()


# for Thread
def daily_operations():
    while True:
        remove_old_contests()

        for tense, lst in contests.items():
            update(lst, tense)

        sleep(60 * 60 * 24)
