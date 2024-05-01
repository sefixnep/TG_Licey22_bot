import json
import sqlite3


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


def contests_filter_tense(tense):
    # Подключение к базе данных
    connection = sqlite3.connect(Paths.DataBase)
    cursor = connection.cursor()

    # Создание запроса
    query = None

    if tense == 'past':
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


print(contests_filter_tense("present"))
