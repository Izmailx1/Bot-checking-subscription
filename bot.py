from telebot import TeleBot
from telebot import types
from telebot.apihelper import ApiTelegramException
import pickle

token = '6150482050:AAH5w6fO_lxK7_9laJHja5rWAbFznxoI-e4'
bot = TeleBot(token)
chats = {}
admins = []
superadmins = [409555770]

with open('chats.pkl', 'rb') as f:
    chats = pickle.load(f)


@bot.message_handler(commands=['start'])
def start_message(message):
    if message.chat.type == 'private':
        if message.chat.id in superadmins:
            admins.append(message.chat.id)
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text='Рассылка по владельцам бота', callback_data='mail_to_owners'))
            keyboard.add(types.InlineKeyboardButton(text='Рассылка по чатам', callback_data='mail_to_chats'))

            bot.send_message(message.chat.id, 'Здравствуй! Я бот для проверки подписки на канал🤖\n'
                                              'Чтобы начать работать, добавьте меня в свою группу и наделите всеми правами\n'
                                              'А после напишите в чате команду \n/startbot @"название канала" через пробел'
                                              ' без кавычек для запуска\n'
                                              'Или команду /stopbot для отключения', reply_markup=keyboard)
        else:
            admins.append(message.chat.id)
            bot.send_message(message.chat.id, 'Здравствуй! Я бот для проверки подписки на канал🤖\n'
                                              'Чтобы начать работать, добавьте меня в свою группу и наделите всеми правами\n'
                                              'А после напишите в чате команду \n/startbot @"название канала" через пробел'
                                              ' без кавычек для запуска\n'
                                              'Или команду /stopbot для отключения')


def go_menu(message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Рассылка по владельцам бота', callback_data='mail_to_owners'))
    keyboard.add(types.InlineKeyboardButton(text='Рассылка по чатам', callback_data='mail_to_chats'))
    bot.send_message(message.chat.id, 'Выберите интересующие Вас действия из меню ниже ⬇',
                     reply_markup=keyboard)


@bot.message_handler(commands=['startbot'])
def start_bot(message):
    global chats
    member = bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status == 'creator' or member.status == 'administrator':
        chats[message.chat.id] = [message.text[10:], message.from_user.id]
        bot.send_message(message.chat.id, 'Функция проверки подписки включена!')
        with open('chats.pkl', 'wb') as f:
            pickle.dump(chats, f)


@bot.message_handler(commands=['stopbot'])
def stop_bot(message):
    global chats
    if chats[message.chat.id][1] == message.from_user.id:
        del chats[message.chat.id]
        with open('chats.pkl', 'wb') as f:
            pickle.dump(chats, f)
        bot.send_message(message.chat.id, 'Функция проверки подписки выключена!')


@bot.message_handler(content_types=['text'])
def check_access(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton(f'Отмена'))
    try:
        if message.from_user.id != chats[message.chat.id][1] or message.text == 'Проверить подписку':
            if not is_subscribed(message):
                bot.delete_message(message.chat.id, message.message_id)
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton(text='Подписаться',
                                                        url=f"https://t.me/{chats[message.chat.id][0][1:]}",
                                                        callback_data='sub_channel_done'))
                print(message.from_user.first_name)
                print(message.from_user.id)
                print(chats[message.chat.id][0])
                bot.send_message(message.chat.id,
                                 f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>\nДля отправки сообщений, вы должны подписаться на канал {chats[message.chat.id][0]}'
                                 , reply_markup=keyboard, parse_mode='HTML')

        elif message.text == 'Рассылка по владельцам бота' and message.chat.id in superadmins:
            bot.send_message(message.chat.id, f'Введите текст рассылки', reply_markup=keyboard)

        elif message.text == 'Рассылка по чатам' and message.chat.id in superadmins:
            bot.send_message(message.chat.id, f'Введите текст рассылки', reply_markup=keyboard)

    except Exception as e:
        print(e)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == 'sub_channel_done':
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data == 'mail_to_chats':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Главное меню', callback_data='menu'))
        bot.send_message(call.message.chat.id, 'Отправьте текст в следующем сообщении, после чего начнется рассылка'
                                               ' этого текста по всем чатам, где есть бот', reply_markup=keyboard)
        bot.register_next_step_handler(call.message, mail_chats)

    elif call.data == 'mail_to_owners':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Главное меню', callback_data='menu'))
        bot.send_message(call.message.chat.id, 'Отправьте текст в следующем сообщении, после чего начнется рассылка'
                                               ' этого текста по всем владельцам бота', reply_markup=keyboard)
        bot.register_next_step_handler(call.message, mail_owners)

    elif call.data == 'menu':
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
        go_menu(call.message)


def is_subscribed(message):
    channel_id = chats[message.chat.id][0]
    user_id = message.from_user.id
    try:
        user_info = bot.get_chat_member(channel_id, user_id)
        if user_info.status == 'left' or user_info.status == 'kicked':
            return False
        return True
    except ApiTelegramException as e:
        if e.result_json['description'] == 'Bad Request: user not found':
            return False


def mail_owners(message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Рассылка по владельцам бота', callback_data='mail_to_owners'))
    keyboard.add(types.InlineKeyboardButton(text='Рассылка по чатам', callback_data='mail_to_chats'))
    for owner in admins:
        print(owner)
        try:
            bot.send_message(owner, message.text)
        except:
            pass
    bot.send_message(message.chat.id, 'Рассылка успешно завершена!\n'
                                      'Чтобы начать работать, добавьте меня в свою группу и наделите всеми правами\n'
                                      'А после напишите в чате команду \n/startbot @"название канала" через пробел'
                                      ' без кавычек для запуска\n'
                                      'Или команду /stopbot для отключения'
                     , reply_markup=keyboard)


def mail_chats(message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Рассылка по владельцам бота', callback_data='mail_to_owners'))
    keyboard.add(types.InlineKeyboardButton(text='Рассылка по чатам', callback_data='mail_to_chats'))
    for chat_id in chats:
        try:
            print(chat_id)
            bot.send_message(chat_id, message.text)
        except:
            pass
    bot.send_message(message.chat.id, 'Рассылка успешно завершена!\n'
                                      'Чтобы начать работать, добавьте меня в свою группу и наделите всеми правами\n'
                                      'А после напишите в чате команду \n/startbot @"название канала" через пробел'
                                      ' без кавычек для запуска\n'
                                      'Или команду /stopbot для отключения'
                     , reply_markup=keyboard)


bot.polling()
