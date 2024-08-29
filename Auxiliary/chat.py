from Auxiliary.utils import *


# Custom functions for buttons
def delete_message(_, message_tg):
    Message.botDeleteMessage(message_tg)


def clear_next_step_handler(_, message_tg):
    bot.clear_step_handler_by_chat_id(
        message_tg.chat.id)  # просто очищаем step_handler
    # ничего не возращаем, чтобы дальше шло как с обычными кнопками


def status_message(to_messages, message_tg):
    status = operations.get_status(message_tg.chat.id)
    if status is None or status == "base":
        return to_messages[0]
    elif status == "editor":
        return to_messages[1]
    elif status == "admin":
        return to_messages[2]


# # Check access

# # # Editor
def check_access_editor(to_messages, message_tg):
    if (operations.get_status(message_tg.chat.id) not in ("admin", "editor") and
            len(to_messages) > 1):  # Проверка наличия доступа
        return to_messages[1]

    return to_messages[0]


# # # Admin
def check_access_admin(to_messages, message_tg):
    if operations.get_status(message_tg.chat.id) != "admin" and len(to_messages) > 1:  # Проверка наличия доступа
        return to_messages[1]

    return to_messages[0]


# Custom functions for messages

# # Contests

# # # Delete contest
def delete_contest_id(message_tg):
    botMessage = message_contest_delete_id.line(message_tg)
    bot.register_next_step_handler(botMessage, delete_contest_result(botMessage))
    return True


def delete_contest_result(botMessage):
    def wrapper(message_tg):
        nonlocal botMessage
        Message.userSendLogger(message_tg)
        Message.botDeleteMessage(message_tg)

        id = message_tg.text.strip()
        if operations.get_contest(id) is not None:
            operations.remove_contests(id)
            message_contest_delete_success.line(botMessage)
        else:
            message_contest_delete_fail.line(botMessage)

    return wrapper


# # # Add contest
def add_contest_name(message_tg):
    botMessage = message_contest_add_name.line(message_tg)
    bot.register_next_step_handler(botMessage, add_contest_date_start(botMessage))
    return True


def add_contest_date_start(botMessage):
    def wrapper(message_tg):
        nonlocal botMessage
        Message.userSendLogger(message_tg)
        Message.botDeleteMessage(message_tg)

        name = message_tg.text.strip()
        botMessage = message_contest_add_date_start.line(botMessage)
        bot.register_next_step_handler(botMessage, add_contest_date_end(botMessage, name))

    return wrapper


def add_contest_date_end(botMessage, name):
    def wrapper(message_tg):
        nonlocal botMessage, name
        Message.userSendLogger(message_tg)
        Message.botDeleteMessage(message_tg)

        date_start = message_tg.text.strip()

        # Проверка на валидную дату
        try:
            date_start = operations.parser.parse(date_start).strftime('%Y-%m-%d')
        except:
            message_contest_add_error.line(botMessage)
            return None

        botMessage = message_contest_add_date_end.line(botMessage)
        bot.register_next_step_handler(botMessage, add_contest_link(botMessage, name, date_start))

    return wrapper


def add_contest_link(botMessage, name, date_start):
    def wrapper(message_tg):
        nonlocal botMessage, name, date_start
        Message.userSendLogger(message_tg)
        Message.botDeleteMessage(message_tg)

        date_end = message_tg.text.strip()

        # Проверка на валидную дату
        try:
            date_end = operations.parser.parse(date_end).strftime('%Y-%m-%d')
        except:
            message_contest_add_error.line(botMessage)
            return None

        botMessage = message_contest_add_link.line(botMessage)
        bot.register_next_step_handler(botMessage, add_contest_tags(botMessage, name, date_start, date_end))

    return wrapper


def add_contest_tags(botMessage, name, date_start, date_end):
    def wrapper(message_tg):
        nonlocal botMessage, name, date_start, date_end
        Message.userSendLogger(message_tg)
        Message.botDeleteMessage(message_tg)

        link = message_tg.text.strip()

        # Проверка на валидную ссылку
        if not is_valid_url(link):
            message_contest_add_error.line(botMessage)
            return None

        botMessage = message_contest_add_tags.line(botMessage)
        bot.register_next_step_handler(botMessage, add_contest_comment(
            botMessage, name, date_start, date_end, link))

    return wrapper


def add_contest_comment(botMessage, name, date_start, date_end, link):
    def wrapper(message_tg):
        nonlocal botMessage, name, date_start, date_end, link
        Message.userSendLogger(message_tg)
        Message.botDeleteMessage(message_tg)

        tags = list(map(str.strip, message_tg.text.lower().split(',')))
        message = Message("Напишите комментарий к конкурсу (необязательно)",
                          ((Button("🔜 Пропустить 🔜",
                                   f"contest_skip_{name}_{date_start}_{date_end}_{link}_{';'.join(tags)}_add",
                                   func=clear_next_step_handler),), (button.cancel_edit_contest,),))
        botMessage = message.line(botMessage)
        bot.register_next_step_handler(botMessage, add_contest_confirm(
            botMessage, name, date_start, date_end, link, tags))

    return wrapper


def add_contest_confirm(botMessage, name, date_start, date_end, link, tags):
    def wrapper(message_tg):
        nonlocal botMessage, name, date_start, date_end, link
        if message_tg is not None:
            Message.userSendLogger(message_tg)
            Message.botDeleteMessage(message_tg)

        comment = message_tg.text.strip() if message_tg is not None else None
        message = Message("*Подтвердите данные*:\n\n"
                          f"*Конкурс*: `{name}`\n"
                          f"├ *Дата проведения*: `{date_start} - {date_end}`\n"
                          f"└ *Предметы*: `{', '.join(tags)}`\n" +
                          (f"\n_Примечание: {comment}_" if comment else ""),
                          ((button.cancel_edit_contest,
                            Button("✔️ Подтвердить ✔️",
                                   f"contest_confirm_{name}_{date_start}_{date_end}_{link}_"
                                   f"{';'.join(tags)}{f'_{comment}' if comment is not None else ''}_add")),
                           ))

        botMessage = message.line(botMessage)

    return wrapper


# # Admin panel

# # # Edit status
def edit_status(message_tg):
    botMessage = message_status_edit.line(message_tg)
    bot.register_next_step_handler(botMessage, status_choice(botMessage))
    return True


def status_choice(botMessage):
    def wrapper(message_tg):
        nonlocal botMessage
        Message.userSendLogger(message_tg)
        Message.botDeleteMessage(message_tg)

        chat_id = message_tg.text.strip()
        message = Message("Выберите статус для пользователя",
                          (
                              (Button("Block", f"block_{chat_id}_edit-status"),
                               Button("Base", f"base_{chat_id}_edit-status")),

                              (Button("Editor", f"editor_{chat_id}_edit-status"),
                               Button("Admin", f"admin_{chat_id}_edit-status")),

                              (button.back_to_admin_panel,)
                          ))

        message.line(botMessage)

    return wrapper

# # # Find contest author
def find_contest_author(message_tg):
    botMessage = message_find_contest_author.line(message_tg)
    bot.register_next_step_handler(botMessage, find_contest_author_answer(botMessage))
    return True

def find_contest_author_answer(botMessage):
    def wrapper(message_tg):
        nonlocal botMessage
        Message.userSendLogger(message_tg)
        Message.botDeleteMessage(message_tg)

        id = message_tg.text.strip()
        message = Message(f"*Chat_id автора*: `{operations.get_contest_author(id)}`",
                          ((button.back_to_admin_panel,),))

        message.line(botMessage)

    return wrapper


# Buttons
button = Button('', '')

# Contact
Button("Контакты", "contacts")

# Start
Button("Новости", "news")
Button("Конкурсы", "contests")

# # Edit
Button("Изменить", "edit_contest", func=check_access_editor)
Button("Изменить", "edit_news", func=check_access_editor)

# Tense contest
Button("Прошедшие", "past_contests_page")
Button("Идущие", "present_contests_page")
Button("Грядущие", "future_contests_page")

# Editor
Button("Удалить", "delete_contest", func=check_access_editor)
Button("Добавить", "add_contest", func=check_access_editor)

# Admin
Button("Админ панель", "admin_panel", func=check_access_admin)

Button("Изменить статус", "edit_status", func=check_access_admin)
Button("Узнать автора конкурса", "find_contest_author", func=check_access_admin)
Button("Рассылка", "mailing", func=check_access_admin)

# Back
Button("🔙 Назад 🔙", "back_to_start", func=status_message)
Button("🔙 Назад 🔙", "back_to_contests")
Button("🔙 Назад 🔙", "back_to_edit_contest", func=check_access_editor)
Button("🔙 Назад 🔙", "back_to_admin_panel", func=check_access_admin)

# Cancel / close
Button("✖️ Отменить ✖️", "cancel_edit_contest", func=clear_next_step_handler)
Button("✖️ Отменить ✖️", "cancel_admin_edit", func=clear_next_step_handler)
Button("✖️ Закрыть ✖️", "close", func=delete_message)

# Messages
message_contacts = Message("*Менеджер*: @Nadezda\_Sibiri", ((button.close,),), button.contacts)

# Start
message_start = Message("*ID:* `<ID>`\n"
                        "_Привет, <USERNAME>!_",
                        ((button.news, button.contests),),
                        button.back_to_start)

message_start_editor = Message("*ID:* `<ID>`\n"
                               "_Привет, <USERNAME>!_\n"
                               "Ваша роль: *Редактор*",
                               ((button.news, button.contests),
                                (button.edit_news, button.edit_contest)),
                               button.back_to_start)

message_start_admin = Message("*ID:* `<ID>`\n"
                              "_Привет, <USERNAME>!_\n"
                              "Ваша роль: *Администратор*",
                              ((button.news, button.contests),
                               (button.edit_news, button.edit_contest),
                               (button.admin_panel,)),
                              button.back_to_start)

# Contest
message_contest_tense = Message("Выбери с какими конкурсами желаешь ознакомиться:",
                                ((button.past_contests_page,
                                  button.present_contests_page,
                                  button.future_contests_page),
                                 (button.back_to_start,)),
                                button.contests, button.back_to_contests)

# # Edit
message_contest_edit = Message("Что вы хотите сделать с конкурсом?",
                               ((button.delete_contest, button.add_contest), (button.back_to_start,)),
                               button.edit_contest,
                               button.cancel_edit_contest,
                               button.back_to_edit_contest)

# # # Delete
message_contest_delete_id = Message("Напишите ID конкурса",
                                    ((button.cancel_edit_contest,),),
                                    button.delete_contest,
                                    func=delete_contest_id)

message_contest_delete_fail = Message("Конкурс с данным ID не найден.",
                                      ((button.back_to_edit_contest,),))

message_contest_delete_success = Message("Конкурс успешно удален!",
                                         ((button.back_to_edit_contest,),))

# # # Add
message_contest_add_name = Message("Напишите название конкурса (Пример: НТО искусственный интеллект)",
                                   ((button.cancel_edit_contest,),),
                                   button.add_contest,
                                   func=add_contest_name)

message_contest_add_date_start = Message("Напишите дату начала *РЕГИСТРАЦИИ* конкурса (Пример: 01.01.2000)",
                                         ((button.cancel_edit_contest,),))

message_contest_add_date_end = Message("Напишите дату конца *РЕГИСТРАЦИИ* конкурса (Пример: 01.01.2000)",
                                       ((button.cancel_edit_contest,),))

message_contest_add_link = Message("Напишите ссылку на конкурс (Пример: https://example.com/)",
                                   ((button.cancel_edit_contest,),))

message_contest_add_tags = Message("Напишите теги конкурса через запятую (Пример: 'математика, информатика')",
                                   ((button.cancel_edit_contest,),))

message_contest_add_success = Message("*Конкурс успешно добавлен!*\n"
                                      "_появится в списке в течении 24 часов_", ((button.back_to_edit_contest,),))

message_contest_add_error = Message("*Ошибка введенных данных*", ((button.back_to_edit_contest,),))

# News
message_news = Message("*В разработке*", ((button.back_to_start,),), button.news)

# # Edit
message_news_edit = Message("*В разработке*", ((button.back_to_start,),), button.edit_news)

# Admin panel
message_admin_panel = Message("Выберите действие:",
                              ((button.edit_status,), (button.find_contest_author,), (button.back_to_start,)),
                              button.admin_panel, button.cancel_admin_edit, button.back_to_admin_panel)

# # Edit status
message_status_edit = Message("Введите ID пользователя:",
                              ((button.cancel_admin_edit,),),
                              button.edit_status,
                              func=edit_status)

message_status_edit_success = Message("*Статус был изменён!*", ((button.back_to_start,),))

# # Find contest author
message_find_contest_author = Message("Введите *ID* конкурса:", ((button.cancel_admin_edit,),),
                                      button.find_contest_author, func=find_contest_author)

# Access
message_no_access = Message("*Отсутствует доступ!*",
                            ((button.back_to_start,),),
                            button.edit_news, button.edit_contest, button.admin_panel,
                            button.delete_contest, button.add_contest)

message_block = Message("*ID:* `<ID>`\n"
                        "*Вы заблокированы!*\n"
                        "_Для разблокироваки /contacts_",
                        ((button.close,),))
