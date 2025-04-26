from threading import Thread

from Auxiliary import contests, news, multitasking
from Auxiliary.chat import *


@bot.message_handler(commands=["start"])
def start(message_tg: telebot.types.Message):
    Message.userSendLogger(message_tg)
    status = operations.get_status(message_tg.chat.id)
    if status == 'admin':
        message = message_start_admin
    elif status == 'editor':
        message = message_start_editor
    elif status == 'block':
        message = message_block
    else:
        if status != "base":
            operations.record_user(message_tg.chat.id, message_tg.chat.username, "base")
        message = message_start

    message.line(message_tg)


@bot.message_handler(commands=["contacts"])
def contacts(message_tg: telebot.types.Message):
    Message.userSendLogger(message_tg)
    message_contacts.line(message_tg)


@bot.callback_query_handler(func=lambda call: True)
def callback_reception(call: telebot.types.CallbackQuery):
    if call.data not in button.callback_data:  # Если кнопка не найдена (скорее всего из-за перезапуска системы)
        start(call.message)
        return None

    data = button.callback_data[call.data]

    if operations.get_status(call.message.chat.id) == 'block' and data != 'close':  # Если пользователь заблокирован
        message_block.line(call.message)
        return None

    commands = ['page', 'add', 'edit-status']

    to_message = None
    from_button = button.get_instance(call.data)

    if from_button:
        to_message = from_button(call.message)

    for command in commands:  # Для кастомной обработки
        if data.split('_')[-1] == command:
            command_data = data.split('_')[:-1]  # Данные передавающиеся кнопкой

            if command == 'page':
                if command_data[-1] == 'contests':
                    if command_data[:2] == ['back', 'to'] or command_data[0] in ('left', 'right'):
                        # (back to / {direction}) {tense} {page} contests
                        page = contests.storage[command_data[-3]][int(command_data[-2])]
                        Message("Выбери конкурс:", page).line(call.message)

                    elif command_data[0] in contests.storage and len(command_data) == 2:
                        # {tense} contests
                        page = contests.storage[command_data[0]][0]
                        Message("Выбери конкурс:", page).line(call.message)

                elif command_data[-1] == "news":
                    if command_data[:2] == ['back', 'to'] or command_data[0] in ('left', 'right'):
                        # (back to / {direction}) {page} news
                        page = news.storage[int(command_data[-2])]
                        Message("Выбери новость:", page).line(call.message)

                    elif len(command_data) == 1:
                        # news
                        page = news.storage[0]
                        Message("Выбери новость:", page).line(call.message)

            if command == 'add':
                if command_data[0] == 'contest':
                    command_data[6] = command_data[6].split(';')

                    if len(command_data) == 7 and command_data[1] == 'skip':
                        # contest skip {name} {date_start} {date_end} {link} {tags}
                        add_contest_confirm(call.message, *command_data[2:])(None)

                    elif len(command_data) == 7 and command_data[1] == 'confirm':
                        # contest confirm {name} {date_start} {date_end} {link} {tags}
                        if (operations.get_status(call.message.chat.id) in
                                ("admin", "editor")):  # Проверка наличия доступа
                            try:
                                operations.record_contest(*command_data[2:], None, call.message.chat.id)
                            except:
                                message_contest_add_error.line(call.message)
                            else:
                                for tense, lst in contests.storage.items():
                                    contests.update(lst, tense)
                                message_contest_add_success.line(call.message)
                        else:
                            message_no_access.line(call.message)

                    elif len(command_data) == 8 and command_data[1] == 'confirm':
                        # contest confirm {name} {date_start} {date_end} {link} {tags} {comment}
                        if (operations.get_status(call.message.chat.id) in
                                ("admin", "editor")):  # Проверка наличия доступа
                            try:
                                operations.record_contest(*command_data[2:], call.message.chat.id)
                            except:
                                message_contest_add_error.line(call.message)
                            else:
                                for tense, lst in contests.storage.items():
                                    contests.update(lst, tense)
                                message_contest_add_success.line(call.message)
                        else:
                            message_no_access.line(call.message)

                elif command_data[0] == 'news':
                    # news confirm {name} {description}
                    if (operations.get_status(call.message.chat.id) in
                            ("admin", "editor")):  # Проверка наличия доступа
                        try:
                            operations.record_news(*command_data[2:5], call.message.chat.id)
                        except:
                            message_news_add_error.line(call.message)
                        else:
                            news.update(news.storage)
                            message_news_add_success.line(call.message)
                    else:
                        message_no_access.line(call.message)

            if command == 'edit-status':
                if len(command_data) == 2:
                    # {status} {chat_id}
                    message = Message(f"<b>Подтвердите</b>:\n\n"
                                      f"<b>Username</b>: <code>" + operations.get_username(command_data[1]) +
                                      "</code>\n"
                                      f"<b>Chat_id</b>: <code>{command_data[1]}</code>\n"
                                      f"<b>Текущий статус</b>: <code>{operations.get_status(command_data[1])}</code>\n"
                                      f"<b>Получаемый статус</b>: <code>{command_data[0]}</code>",
                                      ((button.cancel_admin_edit,
                                        Button("✔️ Подтвердить ✔️",
                                               f"{'_'.join(command_data)}_confirm_{command}")),))

                    message.line(call.message)

                if len(command_data) == 3 and command_data[2] == 'confirm':
                    # {status} {chat_id} confirm
                    if operations.get_status(call.message.chat.id) == 'admin':
                        operations.record_user(command_data[1], None, command_data[0])
                        message_status_edit_success.line(call.message)
                    else:
                        message_no_access.line(call.message)

            break
    else:
        if to_message is not None and to_message(
                call.message) is None:  # Вызываем функцию, если там нет return, то делаем old_line
            to_message.line(call.message)  # Выводить сообщение к которому ведет кнопка

    bot.answer_callback_query(callback_query_id=call.id, show_alert=False)


@bot.message_handler(content_types=['text'])
def watch(message_tg: telebot.types.Message):
    Message.userSendLogger(message_tg)


if __name__ == '__main__':
    Thread(name='Daily_operations', target=multitasking.daily_operations, daemon=None).start()

    print(f"Version: {config.version}")
    print(f"link: https://t.me/{config.Bot}")
    logger.info(f'{config.Bot} start')

bot.infinity_polling()  # logger_level=None
