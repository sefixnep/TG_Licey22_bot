# Project
version = "1.0"

# Bot
Bot = "TG_Licey22_bot"
BOT_TOKEN = "6365090441:AAEcrGVLXbwC--fyNhL73f_QAluVScxQtj8"

length_callback = 10

# Contests
page_shape_contests = [2, 2]  # размерность матрицы с конкурсами на каждой странице
contest_indices = ['id', 'name', 'date_start', 'date_end', 'link', 'tags', 'comment', 'author']
contest_removal_day = 30 * 6

# News
news_indices = ['id', 'name', 'comment', 'date']
news_removal_day = 1

# Path
class Paths:
    DataBase = "../TG_Licey22_bot/Auxiliary/DataBase/DataBase.db"  # Для хостинга полный путь
