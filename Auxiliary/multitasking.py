from Auxiliary import contests, news
from Auxiliary.DataBase import operations
from time import sleep


def daily_operations():
    while True:
        operations.remove_old_contests()
        operations.remove_old_news()

        sleep(60 * 60 * 24)
