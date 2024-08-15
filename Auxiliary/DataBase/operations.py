from datetime import datetime, timedelta
from Auxiliary import config
from dateutil import parser

import json
import sqlite3
import telebot.types


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
      "link" TEXT NOT NULL,
      "tags" JSON NOT NULL,
      "comment" TEXT
    );
    """)

    # Создание таблицы "users", если она не существует
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS "users" (
        "id" TEXT NOT NULL UNIQUE,
        "username" TEXT,
        "status" TEXT NOT NULL,
        PRIMARY KEY("id")
    );
    """)

    # Сохранение изменений
    connection.commit()

    # Закрытие соединения
    connection.close()


# Contests
def get_contest(id: str):
    # Подключение к базе данных
    connection = sqlite3.connect(Paths.DataBase)
    cursor = connection.cursor()

    # Находим нужный конкурс по id
    cursor.execute("SELECT * FROM contests WHERE id = ?", (id,))

    # Достаем данные из таблицы и преобразуем теги
    contest = cursor.fetchone()
    contest = ((contest[:config.contest_indices.index('tags')] +
                (json.loads(contest[config.contest_indices.index('tags')]),) +
                contest[config.contest_indices.index('tags') + 1:])) if contest is not None else None

    # Закрытие соединения
    connection.close()

    return contest


def record_contest(name: str, date_start: str, date_end: str, link: str, tags: list, comment=None):
    # Преобразование данных в формат, подходящий для SQLite
    date_start, date_end = (parser.parse(date).strftime('%Y-%m-%d') for date in (date_start, date_end))
    assert datetime.strptime(date_start, '%Y-%m-%d') < datetime.strptime(date_end, '%Y-%m-%d'), \
        "date_start must be before date_end"

    tags = json.dumps(list(map(str.lower, tags)))

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
              "link",
              "tags",
              "comment"
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """, (name, date_start, date_end, link, tags, comment))

        # Сохранение изменений
        connection.commit()

    # Закрытие соединения
    connection.close()


def remove_contests(id: str):
    # Подключение к базе данных
    connection = sqlite3.connect(Paths.DataBase)
    cursor = connection.cursor()

    # Выполнение запроса к базе данных
    cursor.execute("""
        DELETE FROM contests 
        WHERE id = ?;
    """, (id,))

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


def contests_filter_tense(tense: str):
    # Подключение к базе данных
    connection = sqlite3.connect(Paths.DataBase)
    cursor = connection.cursor()

    # Создание запроса
    query = None

    if tense == 'all':
        query = "SELECT * FROM contests ORDER BY date_start ASC"
    elif tense == 'past':
        query = "SELECT * FROM contests WHERE date_end < CURRENT_TIMESTAMP ORDER BY date_end DESC"
    elif tense == 'present':
        query = ("SELECT * FROM contests WHERE date_start < CURRENT_TIMESTAMP AND CURRENT_TIMESTAMP < date_end "
                 "ORDER BY date_start ASC")
    elif tense == 'future':
        query = "SELECT * FROM contests WHERE CURRENT_TIMESTAMP < date_start ORDER BY date_start ASC"

    assert query is not None, "tense must be all/past/present/future"

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


# Users
def get_user(chat_id: str):
    # Подключение к базе данных
    connection = sqlite3.connect(Paths.DataBase)
    cursor = connection.cursor()

    # Находим нужный статус по chat_id
    cursor.execute("SELECT status FROM users WHERE id = ?", (chat_id,))

    status = cursor.fetchone()

    # Закрытие соединения
    connection.close()

    return status[0] if status is not None else None


def assign_user(message_tg: telebot.types.Message, status: str):
    # Проверка
    assert status in ("base", "editor", "admin"), "status must be base/editor/admin"

    # Создание переменных
    chat_id = message_tg.chat.id
    username = message_tg.chat.username

    # Подключение к базе данных
    connection = sqlite3.connect(Paths.DataBase)
    cursor = connection.cursor()

    # Получим нынешний статус
    temp = get_user(chat_id)

    # Запись данных в таблицу users
    if temp is None and status:
        cursor.execute("""
        INSERT INTO "users" (
          "id",
          "username",
          "status"
        )
        VALUES (?, ?, ?)
        """, (chat_id, username, status))
    elif temp is not None and status:
        cursor.execute("UPDATE users SET status = ?, username = ? WHERE id = ?", (status, username, chat_id))
    elif temp is not None and not status:
        cursor.execute("DELETE FROM users WHERE id = ?", (chat_id,))

    # Сохранение изменений
    connection.commit()

    # Закрытие соединения
    connection.close()
