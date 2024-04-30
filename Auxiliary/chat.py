import telebot
from loguru import logger
from Auxiliary import config

bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode='html')


class Message:
    def __init__(self, text: str, buttons=None, *from_buttons, func=lambda *args: None):
        self.__text = text  # Текст сообщения
        self.__buttons = buttons  # Двумерный кортеж с кнопками в виде InlineKeyboardButton
        self.__board_tg = None  # Клавиатура кнопок под сообщением: InlineKeyboardMarkup
        if buttons:
            self.__board_tg = telebot.types.InlineKeyboardMarkup()
            for row in (map(lambda x: x.button_tg, buttons1D) for buttons1D in buttons):
                self.__board_tg.row(*row)
        for from_button in from_buttons:  # Кнопки которые ведут к этому сообщению
            from_button.to_messages += (self,)
        self.__func = func  # Функция, которая должна происходить при вызове сообщения

    def __call__(self, *args):
        return self.__func(*args)

    def __getitem__(self, item):
        return self.__buttons[item[0]][item[1]]

    def new_line(self, message_tg, delete_message=True, userSendLogger=True):
        if userSendLogger:
            self.userSendLogger(message_tg)
        if delete_message:
            bot.delete_message(message_tg.chat.id, message_tg.id)
        return self.__botSendMessage(message_tg)

    def old_line(self, message_tg, text=None, userSendLogger=False):
        if userSendLogger:
            self.userSendLogger(message_tg, text)
        return self.__botEditMessage(message_tg)

    @staticmethod
    def __trueText(text, message_tg):
        return text.replace("<ID>", str(message_tg.chat.id)).replace("<USERNAME>", message_tg.chat.username)

    @staticmethod
    def userSendLogger(message_tg, text=None):
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

    def __botSendMessage(self, message_tg, parse_mode='MARKDOWN', indent=3):
        text = self.__trueText(self.__text, message_tg)
        botMessage = bot.send_message(chat_id=message_tg.chat.id, text=text, reply_markup=self.__board_tg,
                                      parse_mode=parse_mode)
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

    def __botEditMessage(self, message_tg, parse_mode='MARKDOWN', indent=3):
        text = self.__trueText(self.__text, message_tg)
        botMessage = bot.edit_message_text(chat_id=message_tg.chat.id, message_id=message_tg.id, text=text,
                                           reply_markup=self.__board_tg,
                                           parse_mode=parse_mode)
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

    def __init__(self, text: str, callback_data: str, *to_messages: Message,
                 func=lambda to_messages, message_tg: None):
        self.text = text  # текст кнопки
        self.callback_data = callback_data  # Скрытые (уникальные) данные, несущиеся кнопкой
        self.button_tg = telebot.types.InlineKeyboardButton(
            self.text, callback_data=self.callback_data)  # кнопка в виде объекта InlineKeyboardButton
        self.to_messages = to_messages  # Сообщения, к которым ведёт кнопка
        self.__func = func  # Функция отбора сообщения из to_messages на основе предыдущего сообщения / вспомогательное
        self.instances.append(self)

    def __call__(self, message_tg,
                 userSendLogger=True) -> Message:  # При вызове кновки отдаем сообщение к которому будем идти
        if userSendLogger:
            Message.userSendLogger(message_tg, f'[{self.text}]')
        if self.__func(self.to_messages, message_tg) is not None:
            return self.__func(self.to_messages, message_tg)
        return self.to_messages[0]

    def __getattr__(self, callback_data):  # выполняем поиск кнопки по её скрытым данным, т.к они уникальные
        for instance in self.instances:
            if instance.callback_data == callback_data:
                return instance


def delete_message(_, message_tg):
    bot.delete_message(message_tg.chat.id, message_tg.id)


def clear_next_step_handler(_, message_tg):
    bot.clear_step_handler_by_chat_id(
        message_tg.chat.id)  # просто очищаем step_handler
    # ничего не возращаем, чтобы дальше шло как с обычными кнопками


# Buttons
button = Button('', '')

# Messages
