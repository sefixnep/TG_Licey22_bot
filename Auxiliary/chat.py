from random import randint

import telebot
from loguru import logger

from Auxiliary import config, functions
from Auxiliary.DataBase import operations

bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode='html')


class Message:
    def __init__(self, text: str, buttons=None, *from_buttons, photo=None, func=lambda *args: None):
        self.__text = text  # Текст сообщения
        self.__photo = photo
        self.__buttons = buttons  # Двумерный кортеж с кнопками в виде InlineKeyboardButton
        self.__board_tg = None  # Клавиатура кнопок под сообщением: InlineKeyboardMarkup
        if buttons:
            self.__board_tg = telebot.types.InlineKeyboardMarkup()
            for row in (map(lambda x: x.button_tg, buttons1D) for buttons1D in buttons):
                self.__board_tg.row(*row)
        for from_button in from_buttons:  # Кнопки, которые ведут к этому сообщению
            from_button.to_messages += (self,)
        self.__func = func  # Функция, которая должна происходить при вызове сообщения

    def __call__(self, *args):
        return self.__func(*args)

    def __getitem__(self, item):
        return self.__buttons[item[0]][item[1]]

    def new_line(self, message_tg: telebot.types.Message, deleting_message=True, userSendLogger=True):
        if userSendLogger:
            self.userSendLogger(message_tg)
        botMessage = self.__botSendMessage(message_tg)
        if deleting_message:
            try:
                bot.delete_message(message_tg.chat.id, message_tg.id)
            except:
                pass

        return botMessage

    def old_line(self, message_tg: telebot.types.Message, text=None, userSendLogger=False):
        if userSendLogger:
            self.userSendLogger(message_tg, text)
        if self.__photo is not None:
            return self.new_line(message_tg)
        return self.__botEditMessage(message_tg)

    @staticmethod
    def __trueText(text, message_tg: telebot.types.Message):
        return (text.replace("<ID>", str(message_tg.chat.id))
                .replace("<USERNAME>", str(message_tg.chat.username if message_tg.chat.username else "User")))

    @staticmethod
    def userSendLogger(message_tg: telebot.types.Message, text=None):
        if text is None:
            if '\n' in message_tg.text:
                logger.info(f'{message_tg.from_user.username} ({message_tg.chat.id}): \n{message_tg.text}')
            else:
                logger.info(f'{message_tg.from_user.username} ({message_tg.chat.id}): {message_tg.text}')
        else:
            if '\n' in text:
                logger.info(f'{message_tg.chat.username} ({message_tg.chat.id}): \n{text}')
            else:
                logger.info(f'{message_tg.chat.username} ({message_tg.chat.id}): {text}')

    def __botSendMessage(self, message_tg: telebot.types.Message, parse_mode='MARKDOWN', indent=3):
        text = self.__trueText(self.__text, message_tg)
        botMessage = bot.send_message(chat_id=message_tg.chat.id, text=text,
                                      reply_markup=self.__board_tg, parse_mode=parse_mode) \
            if self.__photo is None else bot.send_photo(
            chat_id=message_tg.chat.id, photo=self.__photo, caption=text,
            reply_markup=self.__board_tg, parse_mode=parse_mode)

        if self.__board_tg is None:
            if '\n' in text:
                logger.info(f"{config.Bot} ({botMessage.chat.username}, {message_tg.chat.id}):\n{text}\n")
            else:
                logger.info(f"{config.Bot} ({botMessage.chat.username}, {message_tg.chat.id}): {text}")
        else:
            reply_markup_text = ''
            for reply_markup1 in botMessage.json['reply_markup']['inline_keyboard']:

                for reply_markup2 in reply_markup1:
                    reply_markup_text += f'[{reply_markup2["text"]}]' + (' ' * indent)
                reply_markup_text = reply_markup_text[:-indent]

                reply_markup_text += '\n'
            reply_markup_text = reply_markup_text[:-1]
            logger.info(
                f"{config.Bot} ({botMessage.chat.username}, {message_tg.chat.id}):\n{text}\n{reply_markup_text}\n")
        return botMessage

    def __botEditMessage(self, message_tg: telebot.types.Message, parse_mode='MARKDOWN', indent=3):
        text = self.__trueText(self.__text, message_tg)
        try:
            botMessage = bot.edit_message_text(chat_id=message_tg.chat.id, message_id=message_tg.id, text=text,
                                               reply_markup=self.__board_tg,
                                               parse_mode=parse_mode)
        except:
            botMessage = bot.send_message(chat_id=message_tg.chat.id, text=text,
                                          reply_markup=self.__board_tg, parse_mode=parse_mode)
            try:
                bot.delete_message(chat_id=message_tg.chat.id, message_id=message_tg.id)
            except:
                pass

        if self.__board_tg is None:
            if '\n' in text:
                logger.info(f"{config.Bot} ({botMessage.chat.username}, {message_tg.chat.id}):\n{text}\n")
            else:
                logger.info(f"{config.Bot} ({botMessage.chat.username}, {message_tg.chat.id}): {text}")
        else:
            reply_markup_text = ''
            for reply_markup1 in botMessage.json['reply_markup']['inline_keyboard']:

                for reply_markup2 in reply_markup1:
                    reply_markup_text += f'[{reply_markup2["text"]}]' + (' ' * indent)
                reply_markup_text = reply_markup_text[:-indent]

                reply_markup_text += '\n'
            reply_markup_text = reply_markup_text[:-1]
            logger.info(
                f"{config.Bot} ({botMessage.chat.username}, {message_tg.chat.id}):\n{text}\n{reply_markup_text}\n")
        return botMessage


class Button:
    instances = list()  # Список со всеми объектами класса
    callback_datas = dict()  # Словарь для хранения callback_data: data

    def __init__(self, text: str, data: str, *to_messages: Message, is_link=False,
                 func=lambda to_messages, message_tg: None):
        self.text = text  # текст кнопки
        if is_link:  # Если кнопка - ссылка
            self.button_tg = telebot.types.InlineKeyboardButton(
                self.text, url=data)  # кнопка в виде объекта InlineKeyboardButton
        else:
            instance = self.__getattr__(data)

            if instance is not None:
                callback_data = instance.callback_data
                self.instances.remove(instance)
            else:
                callback_data = self.get_callback_data()
                self.callback_datas[callback_data] = data
            self.instances.append(self)

            self.callback_data = callback_data  # Скрытые (уникальные) данные, несущиеся кнопкой
            self.button_tg = telebot.types.InlineKeyboardButton(
                self.text, callback_data=self.callback_data)  # кнопка в виде объекта InlineKeyboardButton
            self.to_messages = to_messages  # Сообщения, к которым ведёт кнопка
            self.__func = func  # Функция отбора сообщения из to_messages на основе предыдущего сообщения /
            # вспомогательное

    def __call__(self, message_tg,
                 userSendLogger=True) -> Message:  # При вызове кновки отдаем сообщение к которому будем идти
        if userSendLogger:
            Message.userSendLogger(message_tg, f'[{self.text}]')
        if self.__func(self.to_messages, message_tg) is not None:
            return self.__func(self.to_messages, message_tg)
        if self.to_messages:
            return self.to_messages[0]

    def __getattr__(self, data):  # выполняем поиск кнопки по её скрытым данным, т.к они уникальные
        for instance in self.instances:
            if self.callback_datas[instance.callback_data] == data:
                return instance

    def get_instance(self, callback_data):
        for instance in self.instances:
            if instance.callback_data == callback_data:
                return instance

    @classmethod
    def get_callback_data(cls):
        length = 10
        callback_data = ''.join(str(randint(0, 9)) for _ in range(length))
        while callback_data in cls.callback_datas:
            callback_data = ''.join(str(randint(0, 9)) for _ in range(length))

        return callback_data


# Custom functions for buttons
def delete_message(_, message_tg):
    bot.delete_message(message_tg.chat.id, message_tg.id)


def clear_next_step_handler(_, message_tg):
    bot.clear_step_handler_by_chat_id(
        message_tg.chat.id)  # просто очищаем step_handler
    # ничего не возращаем, чтобы дальше шло как с обычными кнопками


def status_message(to_messages, message_tg):
    status = operations.get_user(message_tg.chat.id)
    if status is None or status == "base":
        return to_messages[0]
    elif status == "editor":
        return to_messages[1]
    elif status == "admin":
        return to_messages[2]


# Custom functions for messages

# # Delete contest
def delete_contest_id(message_tg):
    Message.userSendLogger(message_tg)
    botMessage = message_contest_delete_id.old_line(message_tg)
    bot.register_next_step_handler(botMessage, delete_contest_result(botMessage))
    return True


def delete_contest_result(botMessage):
    def wrapper(message_tg):
        nonlocal botMessage
        Message.userSendLogger(message_tg)
        bot.delete_message(message_tg.chat.id, message_tg.id)

        id = message_tg.text.strip()
        if operations.get_contest(id) is not None:
            operations.remove_contests(id)
            message_contest_delete_success.old_line(botMessage)
        else:
            message_contest_delete_fail.old_line(botMessage)

    return wrapper


# # Add contest
def add_contest_name(message_tg):
    Message.userSendLogger(message_tg)
    botMessage = message_contest_add_name.old_line(message_tg)
    bot.register_next_step_handler(botMessage, add_contest_date_start(botMessage))
    return True


def add_contest_date_start(botMessage):
    def wrapper(message_tg):
        nonlocal botMessage
        Message.userSendLogger(message_tg)
        bot.delete_message(message_tg.chat.id, message_tg.id)

        name = message_tg.text.strip()
        botMessage = message_contest_add_date_start.old_line(botMessage)
        bot.register_next_step_handler(botMessage, add_contest_date_end(botMessage, name))

    return wrapper


def add_contest_date_end(botMessage, name):
    def wrapper(message_tg):
        nonlocal botMessage, name
        Message.userSendLogger(message_tg)
        bot.delete_message(message_tg.chat.id, message_tg.id)

        date_start = message_tg.text.strip()

        # Проверка на валидную дату
        try:
            date_start = operations.parser.parse(date_start).strftime('%Y-%m-%d')
        except:
            message_contest_add_error.old_line(botMessage)
            return None

        botMessage = message_contest_add_date_end.old_line(botMessage)
        bot.register_next_step_handler(botMessage, add_contest_link(botMessage, name, date_start))

    return wrapper


def add_contest_link(botMessage, name, date_start):
    def wrapper(message_tg):
        nonlocal botMessage, name, date_start
        Message.userSendLogger(message_tg)
        bot.delete_message(message_tg.chat.id, message_tg.id)

        date_end = message_tg.text.strip()

        # Проверка на валидную дату
        try:
            date_end = operations.parser.parse(date_end).strftime('%Y-%m-%d')
        except:
            message_contest_add_error.old_line(botMessage)
            return None

        botMessage = message_contest_add_link.old_line(botMessage)
        bot.register_next_step_handler(botMessage, add_contest_tags(botMessage, name, date_start, date_end))

    return wrapper


def add_contest_tags(botMessage, name, date_start, date_end):
    def wrapper(message_tg):
        nonlocal botMessage, name, date_start, date_end
        Message.userSendLogger(message_tg)
        bot.delete_message(message_tg.chat.id, message_tg.id)

        link = message_tg.text.strip()

        # Проверка на валидную ссылку
        if not functions.is_valid_url(link):
            message_contest_add_error.old_line(botMessage)
            return None

        botMessage = message_contest_add_tags.old_line(botMessage)
        bot.register_next_step_handler(botMessage, add_contest_comment(
            botMessage, name, date_start, date_end, link))

    return wrapper


def add_contest_comment(botMessage, name, date_start, date_end, link):
    def wrapper(message_tg):
        nonlocal botMessage, name, date_start, date_end, link
        Message.userSendLogger(message_tg)
        bot.delete_message(message_tg.chat.id, message_tg.id)

        tags = message_tg.text.strip().lower().split(', ')
        message = Message("Напишите комментарий к конкурсу (необязательно)",
                          ((Button("🔜 Пропустить 🔜",
                                   f"contest_skip_{name}_{date_start}_{date_end}_{link}_{';'.join(tags)}_add",
                                   func=clear_next_step_handler),), (button.cancel_edit_contest,),))
        botMessage = message.old_line(botMessage)
        bot.register_next_step_handler(botMessage, add_contest_confirm(
            botMessage, name, date_start, date_end, link, tags))

    return wrapper


def add_contest_confirm(botMessage, name, date_start, date_end, link, tags):
    def wrapper(message_tg):
        nonlocal botMessage, name, date_start, date_end, link
        if message_tg is not None:
            Message.userSendLogger(message_tg)
            bot.delete_message(message_tg.chat.id, message_tg.id)

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

        botMessage = message.old_line(botMessage)

    return wrapper


# Buttons
button = Button('', '')

Button("Новости", "news")
Button("Конкурсы", "contests_tense")

Button("Изменить", "news_edit")
Button("Изменить", "contests_edit")
Button("Изменить редакторов", "editors_edit")

Button("Удалить", "delete_contest")
Button("Добавить", "add_contest")

Button("Прошедшие", "past_contests")
Button("Идущие", "present_contests")
Button("Грядущие", "future_contests")

Button("🔙 Назад 🔙", "back_to_start", func=status_message)
Button("🔙 Назад 🔙", "back_to_contests_tense")
Button("🔙 Назад 🔙", "back_to_contests_edit")

Button("✖️ Отменить ✖️", "cancel_edit_contest", func=clear_next_step_handler)
Button("✖️ Закрыть ✖️", "close", func=delete_message)

# Messages
message_contacts = Message("*Менеджер*: @Nadezda\_Sibiri", ((button.close,),))

# Start messages
message_start = Message("*ID:* `<ID>`\n"
                        "_Привет, <USERNAME>!_",
                        ((button.news, button.contests_tense),),
                        button.back_to_start)

message_start_editor = Message("*ID:* `<ID>`\n"
                               "_Привет, <USERNAME>!_\n"
                               "*Твоя роль:* `Редактор`",
                               ((button.news, button.contests_tense),
                                (button.news_edit, button.contests_edit)),
                               button.back_to_start)

message_start_admin = Message("*ID:* `<ID>`\n"
                              "_Привет, <USERNAME>!_\n"
                              "Твоя роль: *Администратор*",
                              ((button.news, button.contests_tense),
                               (button.news_edit, button.contests_edit),
                               (button.editors_edit,)),
                              button.back_to_start)

# Contest messages
message_contest_tense = Message("Выбери с какими конкурсами желаешь ознакомиться:",
                                ((button.past_contests, button.present_contests, button.future_contests),
                                 (button.back_to_start,)),
                                button.contests_tense, button.back_to_contests_tense)

# # Edit
message_contest_edit = Message("Что вы хотите сделать с конкурсом?",
                               ((button.delete_contest, button.add_contest), (button.back_to_start,)),
                               button.contests_edit,
                               button.cancel_edit_contest,
                               button.back_to_contests_edit)

# # # Delete
message_contest_delete_id = Message("Напишите ID конкурса",
                                    ((button.cancel_edit_contest,),),
                                    button.delete_contest,
                                    func=delete_contest_id)

message_contest_delete_fail = Message("Конкурс с данным ID не найден.",
                                      ((button.back_to_contests_edit,),))

message_contest_delete_success = Message("Конкурс успешно удален!",
                                         ((button.back_to_contests_edit,),))

# # # Add
message_contest_add_name = Message("Напишите название конкурса (Пример: НТО искусственный интеллект)",
                                   ((button.cancel_edit_contest,),),
                                   button.add_contest,
                                   func=add_contest_name)

message_contest_add_date_start = Message("Напишите дату начала конкурса (Пример: 01.01.2000)",
                                         ((button.cancel_edit_contest,),))

message_contest_add_date_end = Message("Напишите дату конца конкурса (Пример: 01.01.2000)",
                                       ((button.cancel_edit_contest,),))

message_contest_add_link = Message("Напишите ссылку на конкурс (Пример: https://example.com/)",
                                   ((button.cancel_edit_contest,),))

message_contest_add_tags = Message("Напишите теги конкурса через запятую (Пример: 'математика, информатика')",
                                   ((button.cancel_edit_contest,),))

message_contest_add_success = Message("*Конкурс успешно добавлен!*\n"
                                      "_появится в списке в течении 24 часов_", ((button.back_to_contests_edit,),))

message_contest_add_error = Message("*Ошибка введенных данных*", ((button.back_to_contests_edit,),))

# News messages
message_news = Message("Выберите событие:", ((button.back_to_start,),), button.news)
