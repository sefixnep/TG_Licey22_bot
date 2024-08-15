from threading import Thread

from Auxiliary import contests, multitasking
from Auxiliary.chat import *


@bot.message_handler(commands=["start"])
def start(message_tg: telebot.types.Message):
    status = operations.get_user(message_tg.chat.id)

    if status == 'admin':
        message_start_admin.new_line(message_tg)
    elif status == 'editor':
        message_start_editor.new_line(message_tg)
    else:
        if status != "base":
            operations.assign_user(message_tg, "base")
        message_start.new_line(message_tg)


@bot.message_handler(commands=["contacts"])
def contacts(message_tg: telebot.types.Message):
    message_contacts.new_line(message_tg)


@bot.callback_query_handler(func=lambda call: True)
def callback_reception(call: telebot.types.CallbackQuery):
    commands = ['contests', 'add']

    if call.data not in button.callback_datas:  # Если кнопка не найдена (скорее всего из-за перезапуска системы)
        start(call.message)
        return None

    to_message = None
    from_button = button.get_instance(call.data)
    data = button.callback_datas[call.data]

    if from_button:
        to_message = from_button(call.message)

    for command in commands:
        if data.split('_')[-1] == command:
            command_data = data.split('_')[:-1]  # Данные передавающиеся кнопкой
            if command == 'contests':
                if command_data[:2] == ['back', 'to'] or command_data[0] in ('left', 'right'):
                    # (back to / {direction}) {tense} {page}
                    Message("Выбери конкурс:", contests.storage[command_data[-2]]
                    [int(command_data[-1])]).old_line(call.message)

                elif command_data[0] in contests.storage and len(command_data) == 1:
                    # {tense}
                    page = tuple()
                    if contests.storage[command_data[0]]:
                        page = contests.storage[command_data[0]][0]

                    Message("Выбери конкурс:", page).old_line(call.message)

            if command == 'add':
                if command_data[0] == 'contest':
                    command_data[6] = command_data[6].split(';')

                    if len(command_data) == 7 and command_data[1] == 'skip':
                        # contest skip name date_start date_end link tags
                        add_contest_confirm(call.message, *command_data[2:])(None)

                    elif len(command_data) == 7 and command_data[1] == 'confirm':
                        # contest confirm name date_start date_end link tags
                        operations.record_contest(*command_data[2:], None)
                        message_contest_add_success.old_line(call.message)

                    elif len(command_data) == 8 and command_data[1] == 'confirm':
                        # contest confirm name date_start date_end link tags comment
                        operations.record_contest(*command_data[2:])
                        message_contest_add_success.old_line(call.message)

            break
    else:
        if to_message is not None and to_message(
                call.message) is None:  # Вызываем функцию, если там нет return, то делаем old_line
            to_message.old_line(call.message)  # Выводить сообщение к которому ведет кнопка

    bot.answer_callback_query(callback_query_id=call.id, show_alert=False)


@bot.message_handler(content_types=['text'])
def watch(message_tg: telebot.types.Message):
    Message.userSendLogger(message_tg)


if __name__ == '__main__':
    operations.Paths.DataBase = "Auxiliary/DataBase/DataBase.db"
    operations.creating_tables()
    Thread(name='Daily_operations', target=multitasking.daily_operations, daemon=None).start()

    print(f"link: https://t.me/{config.Bot}")
    logger.info(f'{config.Bot} start')

bot.infinity_polling()
