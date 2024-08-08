import json
import sqlite3

from time import sleep
from datetime import datetime, timedelta
from dateutil import parser
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
      "link" TEXT NOT NULL,
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


def record_contest(name: str, date_start: str, date_end: str, link: str, tags: list, comment=None):
    # Преобразование данных в формат, подходящий для SQLite
    date_start, date_end = (parser.parse(date).strftime('%Y-%m-%d') for date in (date_start, date_end))
    assert datetime.strptime(date_start, '%Y-%m-%d') < datetime.strptime(date_end, '%Y-%m-%d'), \
        "Дата начала должна быть раньше даты конца"

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


def update(lst: list, tense):
    lst.clear()
    contests_tense = contests_filter_tense(tense)
    amount_pages = ceil(len(contests_tense) / (config.page_shape_contests[0] * config.page_shape_contests[1]))

    if amount_pages == 0:
        lst.append(((button.back_to_contests_tense,),))
        return None

    def leafing(number):
        if amount_pages == 1:
            return ((button.back_to_contests_tense,),)
        elif amount_pages > 1 and number == 0:
            return ((button.back_to_contests_tense,
                     Button(" >> ", f"right_{tense}_{number + 1}_contests")),)
        elif amount_pages > 1 and number == amount_pages - 1:
            return ((Button(" << ", f"left_{tense}_{number - 1}_contests"),
                     button.back_to_contests_tense,),)
        else:
            return ((Button(" << ", f"left_{tense}_{number - 1}_contests"),
                     button.back_to_contests_tense,
                     Button(" >> ", f"right_{tense}_{number + 1}_contests")),)

    for page_number in range(amount_pages):
        Button("🔙 Назад 🔙", f'back_to_{tense}_{page_number}_contests')
        page = tuple()
        for i in range(config.page_shape_contests[0]):
            line = tuple()
            for j in range(config.page_shape_contests[1]):
                count = (page_number * config.page_shape_contests[0] * config.page_shape_contests[1] + i *
                         config.page_shape_contests[1] + j)
                if len(contests_tense) == count:  # Если все конкурсы размещены
                    if j:  # Если на строчке есть конкурсы
                        page += (line,)
                    page += leafing(page_number)
                    lst.append(page)
                    return None

                contest = contests_tense[count]
                callback_data = f'{contest[config.contest_indices.index("id")]}_contest'

                dates = [datetime.strptime(contest[config.contest_indices.index(mode)], "%Y-%m-%d")
                         .strftime("%d.%m.%Y") for mode in ("date_start", "date_end")]
                comment = contest[config.contest_indices.index('comment')]

                Button(contest[config.contest_indices.index('name')], callback_data)
                Message(f"*Конкурс*: `{contest[config.contest_indices.index('name')]}`\n"
                        f"├ *Дата проведения*: `{' - '.join(dates)}`\n"
                        f"└ *Предметы*: `{', '.join(contest[config.contest_indices.index('tags')])}`\n" +
                        (f"\n_Примечание: {comment}_" if comment else ""),
                        ((Button("Перейти", contest[config.contest_indices.index('link')], is_link=True),),
                         (getattr(button, f'back_to_{tense}_{len(lst)}_contests'),),),
                        getattr(button, callback_data))

                line += (getattr(button, callback_data),)
            page += (line,)

        page += leafing(page_number)
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
