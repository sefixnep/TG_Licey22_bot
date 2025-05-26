import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Project
version = "1.0"

# Bot
Bot = "TG_Licey22_bot"
BOT_TOKEN = os.getenv('BOT_TOKEN')

length_callback = 10

# Contests
page_shape_contests = [2, 2]  # размерность матрицы с конкурсами на каждой странице
contest_indices = ['id', 'name', 'date_start', 'date_end', 'link', 'tags', 'comment', 'author']
contest_removal_day = 30 * 6

# News
page_shape_news = [2, 2]  # размерность матрицы с новостями на каждой странице
news_indices = ['id', 'name', 'description', 'date', 'author']
news_removal_day = 2

# Path
class Paths:
    DataBase = "../TG_Licey22_bot/Auxiliary/DataBase/DataBase.db"  # Для хостинга полный путь
