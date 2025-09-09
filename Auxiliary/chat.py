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
    if operations.get_status(message_tg.chat.id) in ("admin", "editor"):  # Проверка наличия доступа
        return to_messages[0]

    return to_messages[-1]


# # # Admin
def check_access_admin(to_messages, message_tg):
    if operations.get_status(message_tg.chat.id) == "admin":  # Проверка наличия доступа
        return to_messages[0]

    return to_messages[-1]


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
        if operations.get_contest(id) is None:
            message_contest_delete_fail.line(botMessage)
        else:
            operations.remove_contests(id)
            message_contest_delete_success.line(botMessage)

            from Auxiliary import contests
            for tense, lst in contests.storage.items():
                contests.update(lst, tense)

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

        # Заменяем разделитель в callback_data на дефис
        name = name.replace('_', '-')
        date_start = date_start.replace('_', '-')
        date_end = date_end.replace('_', '-')
        link = link.replace('_', '-')
        tags = [tag.replace('_', '-') for tag in tags]

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
        nonlocal botMessage, name, date_start, date_end, link, tags
        if message_tg is not None:
            Message.userSendLogger(message_tg)
            Message.botDeleteMessage(message_tg)

        comment = message_tg.text.strip() if message_tg is not None else None
        message = Message("<b>Подтвердите данные</b>:\n\n"
                          f"<b>Конкурс</b>: <code>{name}</code>\n"
                          f"├ <b>Дата проведения</b>: <code>{date_start} - {date_end}</code>\n"
                          f"└ <b>Предметы</b>: <code>{', '.join(tags)}</code>\n" +
                          (f"\n_Примечание: {comment}_" if comment else ""),
                          ((button.cancel_edit_contest,
                            Button("✔️ Подтвердить ✔️",
                                   f"contest_confirm_{name}_{date_start}_{date_end}_{link}_"
                                   f"{';'.join(tags)}{f'_{comment}' if comment is not None else ''}_add")),
                           ))

        message.line(botMessage)

    return wrapper

# # News

# # # Delete news
def delete_news_id(message_tg):
    botMessage = message_news_delete_id.line(message_tg)
    bot.register_next_step_handler(botMessage, delete_news_result(botMessage))
    return True


def delete_news_result(botMessage):
    def wrapper(message_tg):
        nonlocal botMessage
        Message.userSendLogger(message_tg)
        Message.botDeleteMessage(message_tg)

        id = message_tg.text.strip()
        if operations.get_news(id) is None:
            message_news_delete_fail.line(botMessage)
        else:
            operations.remove_news(id)
            message_news_delete_success.line(botMessage)

            from Auxiliary import news
            news.update(news.storage)

    return wrapper


# # # Add news
def add_news_name(message_tg):
    botMessage = message_news_add_name.line(message_tg)
    bot.register_next_step_handler(botMessage, add_news_description(botMessage))
    return True


def add_news_description(botMessage):
    def wrapper(message_tg):
        nonlocal botMessage
        Message.userSendLogger(message_tg)
        Message.botDeleteMessage(message_tg)

        name = message_tg.text.strip()
        botMessage = message_contest_add_description.line(botMessage)
        bot.register_next_step_handler(botMessage, add_news_confirm(botMessage, name))

    return wrapper


def add_news_confirm(botMessage, name):
    def wrapper(message_tg):
        nonlocal botMessage, name
        if message_tg is not None:
            Message.userSendLogger(message_tg)
            Message.botDeleteMessage(message_tg)

        description = message_tg.text.strip()

        # Заменяем разделитель в callback_data на дефис
        name = name.replace('_', '-')
        description = description.replace('_', '-')

        Message("<b>Подтвердите данные</b>:\n\n"
              f"<b>Новость</b>: <code>{name}</code>\n"
              f"<b>Описание</b>: <code>{description}</code>\n",
              ((
                button.cancel_edit_news,
                Button("✔️ Подтвердить ✔️", f"news_confirm_{name}_{description}_add")),
               ),).line(botMessage)

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

# # # Find author

# # # # Contest
def find_author_contest(message_tg):
    botMessage = message_find_author_contest.line(message_tg)
    bot.register_next_step_handler(botMessage, find_contest_author_answer(botMessage))
    return True

def find_contest_author_answer(botMessage):
    def wrapper(message_tg):
        nonlocal botMessage
        Message.userSendLogger(message_tg)
        Message.botDeleteMessage(message_tg)

        id = message_tg.text.strip()

        chat_id = operations.get_contest_author(id)
        username = operations.get_username(chat_id)

        message = Message(f"<u><b>Автор</b></u>:\n"
                          f"├ <b>Username</b>: @{username}\n"
                          f"└ <b>Chat_id</b>: <code>{chat_id}</code>",
                          ((button.back_to_admin_panel,),))

        message.line(botMessage)

    return wrapper

# # # # News
def find_author_news(message_tg):
    botMessage = message_find_author_news.line(message_tg)
    bot.register_next_step_handler(botMessage, find_news_author_answer(botMessage))
    return True

def find_news_author_answer(botMessage):
    def wrapper(message_tg):
        nonlocal botMessage
        Message.userSendLogger(message_tg)
        Message.botDeleteMessage(message_tg)

        id = message_tg.text.strip()

        chat_id = operations.get_news_author(id)
        username = operations.get_username(chat_id)

        message = Message(f"<u><b>Автор</b></u>:\n"
                          f"├ <b>Username</b>: @{username}\n"
                          f"└ <b>Chat_id</b>: <code>{chat_id}</code>",
                          ((button.back_to_admin_panel,),))

        message.line(botMessage)

    return wrapper

# Buttons
button = Button('', '')

# Contact
Button("Контакты", "contacts")

# Start
Button("Новости", "news_page")
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

Button("Удалить", "delete_news", func=check_access_editor)
Button("Добавить", "add_news", func=check_access_editor)

# Admin
Button("Админ панель", "admin_panel", func=check_access_admin)

Button("Изменить статус", "edit_status", func=check_access_admin)

Button("Узнать автора", "find_author", func=check_access_admin)
Button("Новости", "find_author_news", func=check_access_admin)
Button("Конкурса", "find_author_contest", func=check_access_admin)

Button("Рассылка", "mailing", func=check_access_admin)

# Back
Button("🔙 Назад 🔙", "back_to_start", func=status_message)
Button("🔙 Назад 🔙", "back_to_contests")
Button("🔙 Назад 🔙", "back_to_edit_contest", func=check_access_editor)
Button("🔙 Назад 🔙", "back_to_edit_news", func=check_access_editor)
Button("🔙 Назад 🔙", "back_to_admin_panel", func=check_access_admin)

# Cancel / close
Button("✖️ Отменить ✖️", "cancel_edit_contest", func=clear_next_step_handler)
Button("✖️ Отменить ✖️", "cancel_edit_news", func=clear_next_step_handler)
Button("✖️ Отменить ✖️", "cancel_admin_edit", func=clear_next_step_handler)
Button("✖️ Отменить ✖️", "cancel_find_author", func=clear_next_step_handler)
Button("✖️ Закрыть ✖️", "close", func=delete_message)

# Messages
message_contacts = Message("<b>Менеджер</b>: @Nadezda_Sibiri\n"
                           "<b>Автор бота</b>: @sefixnep",
                           ((button.close,),), 
                           button.contacts)

# Start
message_start = Message("<b>ID:</b> <code><ID></code>\n"
                        "<i>Привет, <USERNAME>!</i>\n",
                        ((button.news_page, button.contests),),
                        button.back_to_start)

message_start_editor = Message("<b>ID:</b> <code><ID></code>\n"
                               "<i>Привет, <USERNAME>!</i>\n"
                               "Ваша роль: <b>Редактор</b>",
                               ((button.news_page, button.contests),
                                (button.edit_news, button.edit_contest)),
                               button.back_to_start)

message_start_admin = Message("<b>ID:</b> <code><ID></code>\n"
                              "<i>Привет, <USERNAME>!</i>\n"
                              "Ваша роль: <b>Администратор</b>",
                              ((button.news_page, button.contests),
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
                               button.edit_contest, button.cancel_edit_contest, button.back_to_edit_contest)

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
message_contest_add_name = Message("Напишите название конкурса: (заголовок)",
                                   ((button.cancel_edit_contest,),),
                                   button.add_contest,
                                   func=add_contest_name)

message_contest_add_date_start = Message("Напишите дату начала <b>РЕГИСТРАЦИИ</b> конкурса (Пример: 01.01.2000)",
                                         ((button.cancel_edit_contest,),))

message_contest_add_date_end = Message("Напишите дату конца <b>РЕГИСТРАЦИИ</b> конкурса (Пример: 01.01.2000)",
                                       ((button.cancel_edit_contest,),))

message_contest_add_link = Message("Напишите ссылку на конкурс (Пример: https://example.com/)",
                                   ((button.cancel_edit_contest,),))

message_contest_add_tags = Message("Напишите теги конкурса через запятую (Пример: 'математика, информатика')",
                                   ((button.cancel_edit_contest,),))

message_contest_add_success = Message("<b>Конкурс успешно добавлен!</b>\n",
                                      ((button.back_to_edit_contest,),))

message_contest_add_error = Message("<b>Ошибка введенных данных</b>",
                                    ((button.back_to_edit_contest,),))

# News

# # Edit
message_news_edit = Message("<b>Что вы хотите сделать с новостью?</b>",
                            ((button.delete_news, button.add_news), (button.back_to_start,),),
                            button.edit_news, button.back_to_edit_news, button.cancel_edit_news)

# # # Delete news
message_news_delete_id = Message("Напишите ID новости",
                              ((button.cancel_edit_news,),),
                              button.delete_news,
                              func=delete_news_id)

message_news_delete_fail = Message("Новость с данным ID не найдена.",
                                      ((button.back_to_edit_news,),))

message_news_delete_success = Message("Новость успешно удалена!",
                                         ((button.back_to_edit_news,),))

# # # Add
message_news_add_name = Message("Напишите название новости: (заголовок)",
                                   ((button.cancel_edit_news,),),
                                   button.add_news,
                                   func=add_news_name)

message_contest_add_description = Message("Напишите описание новости: (основной текст)",
                                         ((button.cancel_edit_news,),))

message_news_add_success = Message("<b>Новость успешно добавлена!</b>\n",
                                   ((button.back_to_edit_news,),))

message_news_add_error = Message("<b>Ошибка введенных данных</b>",
                                 ((button.back_to_edit_news,),))

# Admin panel
message_admin_panel = Message("Выберите действие:",
                              (
                                  (button.edit_status,),
                                  (button.find_author,),
                                  (button.back_to_start,)
                              ),
                              button.admin_panel, button.cancel_admin_edit, button.back_to_admin_panel,
                              button.cancel_find_author)

# # Edit status
message_status_edit = Message("Введите ID пользователя:",
                              ((button.cancel_admin_edit,),),
                              button.edit_status,
                              func=edit_status)

message_status_edit_success = Message("<b>Статус был изменён!</b>", ((button.back_to_start,),))

# # Find author
message_find_author = Message("Автора чего вы хотите узнать?",
                              ((button.find_author_news, button.find_author_contest),
                               (button.back_to_admin_panel,)),
                              button.find_author,)

message_find_author_contest = Message("Введите <b>ID</b> конкурса:", ((button.cancel_find_author,),),
                                      button.find_author_contest, func=find_author_contest)

message_find_author_news = Message("Введите <b>ID</b> новости:", ((button.cancel_find_author,),),
                                      button.find_author_news, func=find_author_news)

# Access
message_no_access = Message("<b>Отсутствует доступ!</b>",
                            ((button.back_to_start,),),
                            button.edit_news, button.edit_contest, button.admin_panel,
                            button.delete_news, button.add_news,
                            button.delete_contest, button.add_contest,
                            button.find_author, button.edit_status,
                            button.find_author_news, button.find_author_contest,
                            button.back_to_edit_news, button.back_to_edit_contest, button.back_to_admin_panel,
                            button.mailing
                            )

message_block = Message("<b>ID:</b> <code><ID></code>\n"
                        "<b>Вы заблокированы!</b>\n"
                        "<i>Для разблокироваки /contacts</i>",
                        ((button.close,),))
