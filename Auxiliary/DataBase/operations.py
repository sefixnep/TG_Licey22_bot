import json
import sqlite3
from datetime import datetime, timedelta

from dateutil import parser

from Auxiliary import config


# noinspection SqlNoDataSourceInspection
def creating_tables():
    # Подключение к базе данных
    connection = sqlite3.connect(config.Paths.DataBase)
    cursor = connection.cursor()

    # Создание таблицы "contests", если она не существует
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS "contests" (
      "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
      "name" VARCHAR(255) NOT NULL,
      "date_start" DATETIME NOT NULL,
      "date_end" DATETIME NOT NULL,
      "link" TEXT NOT NULL,
      "tags" JSON NOT NULL,
      "comment" TEXT,
      "author"	TEXT NOT NULL
    );
    """)

    # Создание таблицы "news", если она не существует
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "news" (
          "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
          "name" VARCHAR(255) NOT NULL,
          "description" TEXT NOT NULL,
          "date" DATETIME NOT NULL,
          "author" TEXT NOT NULL
        );
        """)

    # Создание таблицы "users", если она не существует
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS "users" (
        "chat_id" TEXT NOT NULL UNIQUE PRIMARY KEY,
        "username" VARCHAR(255),
        "status" TEXT NOT NULL
    );
    """)

    # Создание таблицы "callback_data", если она не существует
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "callback_data" (
            "callback" TEXT NOT NULL UNIQUE,
            "data" TEXT NOT NULL PRIMARY KEY UNIQUE
        );
        """)

    # Сохранение изменений
    connection.commit()

    # Закрытие соединения
    connection.close()


# Contests
def get_contest(id: str | int):
    # Подключение к базе данных
    connection = sqlite3.connect(config.Paths.DataBase)
    cursor = connection.cursor()

    # Находим нужный конкурс по id
    cursor.execute("SELECT * FROM contests WHERE id = ?", (id,))

    # Достаем данные из таблицы и преобразуем теги
    contest = cursor.fetchone()
    contest = ((contest[:config.contest_indices.index('tags')] +
                (json.loads(contest[config.contest_indices.index('tags')]),) +
                contest[config.contest_indices.index('tags') + 1:config.contest_indices.index('author')])) \
        if contest is not None else None

    # Закрытие соединения
    connection.close()

    return contest


def get_contest_author(id: str | int):
    # Подключение к базе данных
    connection = sqlite3.connect(config.Paths.DataBase)
    cursor = connection.cursor()

    # Находим author по id
    cursor.execute("SELECT author FROM contests WHERE id = ?", (id,))

    status = cursor.fetchone()

    # Закрытие соединения
    connection.close()

    return status[0] if status is not None else None


def record_contest(name: str, date_start: str, date_end: str, link: str, tags: list, comment: str | None, author: str | int):
    # Преобразование данных в формат, подходящий для SQLite
    date_start, date_end = (parser.parse(date).strftime('%Y-%m-%d') for date in (date_start, date_end))
    assert datetime.strptime(date_start, '%Y-%m-%d') <= datetime.strptime(date_end, '%Y-%m-%d'), \
        "date_start must be before date_end"

    tags = json.dumps(list(map(str.lower, tags)))

    # Подключение к базе данных
    connection = sqlite3.connect(config.Paths.DataBase)
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
              "comment",
              "author"
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, date_start, date_end, link, tags, comment, author))

        # Сохранение изменений
        connection.commit()

    # Закрытие соединения
    connection.close()


def remove_contests(id: str | int):
    # Подключение к базе данных
    connection = sqlite3.connect(config.Paths.DataBase)
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
    connection = sqlite3.connect(config.Paths.DataBase)
    cursor = connection.cursor()

    # Определение текущей даты и даты, от config.contest_removal_day дней назад
    current_date = datetime.now()
    thirty_days_ago = current_date - timedelta(days=config.contest_removal_day)

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
    connection = sqlite3.connect(config.Paths.DataBase)
    cursor = connection.cursor()

    # Создание запроса
    query = None

    if tense == 'all':
        query = "SELECT * FROM contests ORDER BY date_start ASC"
    elif tense == 'past':
        query = "SELECT * FROM contests WHERE date_end < CURRENT_TIMESTAMP ORDER BY date_end DESC"
    elif tense == 'present':
        query = ("SELECT * FROM contests WHERE date_start <= CURRENT_TIMESTAMP AND CURRENT_TIMESTAMP <= date_end "
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


# News
def get_all_news():
    # Подключение к базе данных
    connection = sqlite3.connect(config.Paths.DataBase)
    cursor = connection.cursor()

    # Находим нужную новость по id
    cursor.execute("SELECT * FROM news")

    # Достаем данные из таблицы и преобразуем теги
    news = cursor.fetchall()
    for i in range(len(news)):
        news[i] = (news[i][:config.news_indices.index("date")] +
                (datetime.strptime(news[i][config.news_indices.index("date")], "%Y-%m-%d %H:%M:%S"),) +
                news[i][config.news_indices.index("date") + 1:])

    # Закрытие соединения
    connection.close()

    return news


def get_news(id: str | int):
    # Подключение к базе данных
    connection = sqlite3.connect(config.Paths.DataBase)
    cursor = connection.cursor()

    # Находим нужную новость по id
    cursor.execute("SELECT * FROM news WHERE id = ?", (id,))

    # Достаем данные из таблицы и преобразуем теги
    news = cursor.fetchone()
    news = (news[:config.news_indices.index("date")] +
            (datetime.strptime(news[config.news_indices.index("date")], "%Y-%m-%d %H:%M:%S"),) +
            news[config.news_indices.index("date") + 1:]) if news is not None else None

    # Закрытие соединения
    connection.close()

    return news

def get_news_author(id: str | int):
    # Подключение к базе данных
    connection = sqlite3.connect(config.Paths.DataBase)
    cursor = connection.cursor()

    # Находим нужную новость по id
    cursor.execute("SELECT author FROM news WHERE id = ?", (id,))

    # Достаем данные из таблицы и преобразуем теги
    author = cursor.fetchone()

    # Закрытие соединения
    connection.close()

    return author[0] if author else None


def record_news(name: str, comment: str, chat_id: str | int):
    # Подключение к базе данных
    connection = sqlite3.connect(config.Paths.DataBase)
    cursor = connection.cursor()

    # Создание переменных
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Ищем такую-же новость
    cursor.execute("SELECT id FROM news WHERE "
                   "name = ? AND "
                   "description = ?", (name, comment))

    # Запись данных в таблицу news если такой новости не было
    if cursor.fetchone() is None:
        cursor.execute("""
            INSERT INTO "news" (
              "name",
              "description",
              "date",
              "author"
            )
            VALUES (?, ?, ?, ?)
        """, (name, comment, date, chat_id))

        # Сохранение изменений
        connection.commit()

    # Закрытие соединения
    connection.close()


def remove_news(id: str | int):
    # Подключение к базе данных
    connection = sqlite3.connect(config.Paths.DataBase)
    cursor = connection.cursor()

    # Выполнение запроса к базе данных
    cursor.execute("""
        DELETE FROM news 
        WHERE id = ?;
    """, (id,))

    # Сохранение изменений
    connection.commit()

    # Закрытие соединения
    connection.close()


def remove_old_news():
    # Подключение к базе данных
    connection = sqlite3.connect(config.Paths.DataBase)
    cursor = connection.cursor()

    # Определение текущей даты и даты, от config.news_removal_day дней назад
    current_date = datetime.now()
    thirty_days_ago = current_date - timedelta(days=config.news_removal_day)

    # Преобразование дат в формат, подходящий для SQLite
    thirty_days_ago_str = thirty_days_ago.strftime('%Y-%m-%d')

    # Выполнение запроса к базе данных
    cursor.execute("""
        DELETE FROM news 
        WHERE date < ?;
    """, (thirty_days_ago_str,))

    # Сохранение изменений
    connection.commit()

    # Закрытие соединения
    connection.close()


# Users
def get_status(chat_id: str | int):
    # Подключение к базе данных
    connection = sqlite3.connect(config.Paths.DataBase)
    cursor = connection.cursor()

    # Находим status по chat_id
    cursor.execute("SELECT status FROM users WHERE chat_id = ?", (chat_id,))

    status = cursor.fetchone()

    # Закрытие соединения
    connection.close()

    return status[0] if status is not None else None


def get_username(chat_id: str | int):
    # Подключение к базе данных
    connection = sqlite3.connect(config.Paths.DataBase)
    cursor = connection.cursor()

    # Находим username по chat_id
    cursor.execute("SELECT username FROM users WHERE chat_id = ?", (chat_id,))

    status = cursor.fetchone()

    # Закрытие соединения
    connection.close()

    return status[0] if status is not None else None


def record_user(chat_id: str | int, username: str | None, status: str):
    # Проверка
    assert status in ("block", "base", "editor", "admin"), "status must be block/base/editor/admin"

    # Подключение к базе данных
    connection = sqlite3.connect(config.Paths.DataBase)
    cursor = connection.cursor()

    # Получим нынешний статус
    temp = get_status(chat_id)

    # Запись данных в таблицу users
    if temp is None and status:
        cursor.execute("""
        INSERT INTO "users" (
          "chat_id",
          "username",
          "status"
        )
        VALUES (?, ?, ?)
        """, (chat_id, username, status))
    elif temp is not None and status:
        if username is None:
            cursor.execute("UPDATE users SET status = ? WHERE chat_id = ?", (status, chat_id))
        else:
            cursor.execute("UPDATE users SET status = ?, username = ? WHERE chat_id = ?",
                           (status, username, chat_id))
    elif temp is not None and not status:
        cursor.execute("DELETE FROM users WHERE chat_id = ?", (chat_id,))

    # Сохранение изменений
    connection.commit()

    # Закрытие соединения
    connection.close()


# Callback_data
def get_callback(data: str):
    # Подключение к базе данных
    connection = sqlite3.connect(config.Paths.DataBase)
    cursor = connection.cursor()

    # Находим нужный callback по data
    cursor.execute("SELECT callback FROM callback_data WHERE data = ?", (data,))

    callback = cursor.fetchone()

    # Закрытие соединения
    connection.close()

    return callback[0] if callback is not None else None


def record_callback_data(callback: str | int, data: str):
    # Подключение к базе данных
    connection = sqlite3.connect(config.Paths.DataBase)
    cursor = connection.cursor()

    # Находим нужный callback по data
    temp = get_callback(data)

    # Запись данных в таблицу callback_data
    if temp is None:
        cursor.execute("""
            INSERT INTO "callback_data" (
              "callback",
              "data"
            )
            VALUES (?, ?)
            """, (callback, data))
    else:
        cursor.execute("UPDATE callback_data SET callback = ? WHERE data = ?",
                       (callback, data))

    # Сохранение изменений
    connection.commit()

    # Закрытие соединения
    connection.close()


if __name__ != '__main__':
    creating_tables()
