import json
import sqlite3

from time import sleep
from datetime import datetime, timedelta
from math import ceil

from Auxiliary import config


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

    # Сохранение изменений
    connection.commit()

    # Закрытие соединения
    connection.close()


def record(name: str, date_start: str, date_end: str, tags: list, comment=None):
    # Подключение к базе данных
    connection = sqlite3.connect(Paths.DataBase)
    cursor = connection.cursor()

    # Запись данных в таблицу "contests"
    cursor.execute("""
    INSERT INTO "contests" (
      "name",
      "date_start",
      "date_end",
      "tags",
      "comment"
    )
    VALUES (?, ?, ?, ?, ?)
    """, (name, date_start, date_end, json.dumps(tags), comment))

    # Сохранение изменений
    connection.commit()

    # Закрытие соединения
    connection.close()


def remove_old_contests():
    # Подключение к базе данных
    connection = sqlite3.connect(Paths.DataBase)
    cursor = connection.cursor()

    # Определение текущей даты и даты, от 30 дней назад
    current_date = datetime.now()
    thirty_days_ago = current_date - timedelta(days=30)

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
        records[i] = records[i][:4] + (json.loads(records[i][4]),) + records[i][5:]

    # Закрытие соединения с базой данных
    connection.close()

    return records


def update(lst: list, tense):
    lst.clear()
    contests = contests_filter_tense(tense)
    for _ in range(ceil(len(contests) / (config.shape[0] * config.shape[1]))):
        page = list()
        for i in range(config.shape[0]):
            temp = list()
            for j in range(config.shape[1]):
                if len(contests) == i * config.shape[1] + j:
                    if j:
                        page.append(temp)
                        lst.append(page)
                    return None
                temp.append(contests[i * config.shape[1] + j])
            page.append(temp)
        lst.append(page)


# for Thread
def remove_old_contests_thread():
    while True:
        remove_old_contests()

        sleep(60 * 60 * 24)
