from Auxiliary import contests
from Auxiliary.DataBase import operations
from time import sleep


def daily_operations():
    while True:
        operations.remove_old_contests()

        for tense, lst in contests.storage.items():
            contests.update(lst, tense)

        sleep(60 * 60 * 24)
