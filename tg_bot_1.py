from math import ceil
import json

import telebot
import config

import pydantic_models
import client


bot = telebot.TeleBot(config.bot_token)


@bot.message_handler(commands=['start'])
def start_message(message):
    try:
        client.create_user({"tg_ID": message.from_user.id, "nick": message.from_user.username})
    except Exception as Ex:
        pass

    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    btn1 = telebot.types.KeyboardButton('Кошелек')
    btn2 = telebot.types.KeyboardButton('Перевести')
    btn3 = telebot.types.KeyboardButton('История')

    markup.add(btn1, btn2, btn3)

    text = f'Привет {message.from_user.full_name}, я твой бот криптокошелек, \n' \
           'у меня ты можешь хранить и отправлять биткоины'

    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(regexp='Кошелек')
def wallet(message):
    wallet = client.get_user_wallet_by_tg_id(message.from_user.id)
    wallet = json.loads(wallet.text)
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)
    text = f'Ваш баланс: {wallet["balance"]/100000000} BTC\n'\
           f'Ваш адрес: {wallet["address"]}'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(regexp='История')
def history(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)
    transactions = client.get_user_transactions(client.get_user_by_tg_id(message.from_user.id)['id'])
    text = f'Ваши транзакции \n{transactions}'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(regexp='Меню')
def menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
    btn1 = telebot.types.KeyboardButton('Кошелек')
    btn2 = telebot.types.KeyboardButton('Перевести')
    btn3 = telebot.types.KeyboardButton('История')
    markup.add(btn1, btn2, btn3)
    text = f'Главное меню'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(regexp='Я в консоли')
def print_me(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)
    print(message.from_user.to_dict())
    text = f'Ты: {message.from_user.to_dict()}'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(func=lambda message: message.from_user.id == config.tg_admin_id and message.text == 'Админка')
def admin_panel(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Общий баланс')
    btn2 = telebot.types.KeyboardButton('Все юзеры')
    btn3 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1, btn2, btn3)
    text = f'Админ-панель'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(func=lambda message: message.from_user.id == config.tg_admin_id and message.text == 'Все юзеры')
def all_users(message):
    users = client.get_users()
    indx = 0
    count = ceil(len(users) / 4)
    text = f'Юзеры:'
    inline_markup = telebot.types.InlineKeyboardMarkup()

    for user in users[indx*4:indx*4 + 4]:
        inline_markup.add(telebot.types.InlineKeyboardButton(text=f'Юзер: {user["tg_ID"]}',
                                                             callback_data=f'user_{user["tg_ID"]}'))

    inline_markup.add(
        telebot.types.InlineKeyboardButton(text=f'{indx + 1}/{count}', callback_data=f' '),
        telebot.types.InlineKeyboardButton(text=f'Вперед', callback_data=f'forward%{indx}%')
    )

    bot.send_message(message.chat.id, text, reply_markup=inline_markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    query_type = call.data.split('_')[0]
    users = client.get_users()

    if '%' in call.data:
        pagination_call = call.data.split('%')
        count = ceil(len(users) / 4)
        indx = int(pagination_call[1])
        text = f'Юзеры:'
    else:
        pagination_call = False

    if pagination_call:
        if pagination_call[0] == 'forward' and indx < count - 1:
            indx += 1
            inline_markup = telebot.types.InlineKeyboardMarkup()
            for user in users[indx*4:indx*4 + 4]:
                inline_markup.add(telebot.types.InlineKeyboardButton(text=f'Юзер: {user["tg_ID"]}',
                                                                     callback_data=f'user_{user["tg_ID"]}'))

            if indx == count - 1:
                inline_markup.add(
                    telebot.types.InlineKeyboardButton(text=f'Назад', callback_data=f'prev%{indx}%'),
                    telebot.types.InlineKeyboardButton(text=f'{indx + 1}/{count}', callback_data=f' '),
                )
            else:
                inline_markup.add(
                    telebot.types.InlineKeyboardButton(text=f'Назад', callback_data=f'prev%{indx}%'),
                    telebot.types.InlineKeyboardButton(text=f'{indx + 1}/{count}', callback_data=f' '),
                    telebot.types.InlineKeyboardButton(text=f'Вперед', callback_data=f'forward%{indx}%')
                )

            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=inline_markup
            )

        if pagination_call[0] == 'prev' and indx > 0:
            indx -= 1
            inline_markup = telebot.types.InlineKeyboardMarkup()
            for user in users[indx*4:indx*4 + 4]:
                inline_markup.add(telebot.types.InlineKeyboardButton(text=f'Юзер: {user["tg_ID"]}',
                                                                     callback_data=f'user_{user["tg_ID"]}'))
            if indx == 0:
                inline_markup.add(
                    telebot.types.InlineKeyboardButton(text=f'{indx + 1}/{count}', callback_data=f' '),
                    telebot.types.InlineKeyboardButton(text=f'Вперед', callback_data=f'forward%{indx}%')
                )
            else:
                inline_markup.add(
                    telebot.types.InlineKeyboardButton(text=f'Назад', callback_data=f'prev%{indx}%'),
                    telebot.types.InlineKeyboardButton(text=f'{indx + 1}/{count}', callback_data=f' '),
                    telebot.types.InlineKeyboardButton(text=f'Вперед', callback_data=f'forward%{indx}%')
                )

            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=inline_markup
            )

    if query_type == 'user':
        user_id = call.data.split('_')[1]
        inline_markup = telebot.types.InlineKeyboardMarkup()
        for user in users:
            if str(user['tg_ID']) == user_id:
                inline_markup.add(telebot.types.InlineKeyboardButton(text='Назад', callback_data='users'),
                                  telebot.types.InlineKeyboardButton(text='Удалить юзера',
                                                                     callback_data=f'delete_user_{user_id}'))
                bot.edit_message_text(text=f'Данные по юзеру: \n'
                                           f'ID: {user["tg_ID"]}\n'
                                           f'Ник: {user.get("nick")}\n'
                                           f'Баланс: {client.get_user_balance_by_id(user["id"])}\n',
                                      chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      reply_markup=inline_markup)
                print(f'Запрошен {user}')
                break

    if query_type == 'users':
        all_users(message=call.message)

    if query_type == 'delete' and call.data.split('_')[1] == 'user':
        user_id = int(call.data.split('_')[2])
        for i, user in enumerate(users):
            if user['tg_ID'] == user_id:
                print(f'Удален юзер: {users[i]}')
                client.delete_user(users.pop(i)["id"])
        all_users(message=call.message)


@bot.message_handler(func=lambda message: message.from_user.id == config.tg_admin_id and message.text == 'Общий баланс')
def total_balance(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Меню')
    btn2 = telebot.types.KeyboardButton('Админка')
    markup.add(btn1, btn2)
    balance = client.get_total_balance()
    text = f'Общий баланс: {balance/100000000} BTC'
    bot.send_message(message.chat.id, text, reply_markup=markup)


states_list = ["ADDRESS", "AMOUNT", "CONFIRM"]
states_of_users = {}


@bot.message_handler(regexp='Перевести')
def start_transaction(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.InlineKeyboardButton('Меню')
    markup.add(btn1)
    text = f'Введите адресс кошелька куда хотите перевести'
    bot.send_message(message.chat.id, text, reply_markup=markup)
    states_of_users[message.from_user.id] = {"STATE": "ADDRESS"}


@bot.message_handler(func=lambda message: states_of_users.get(message.from_user.id)["STATE"] == "ADDRESS")
def get_amount_of_transaction(message):
    if message.text == 'Меню':
        del states_of_users[message.from_user.id]
        menu(message)
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)
    text = f'Введите сумму в сатоши, которую хотите перевести: '
    bot.send_message(message.from_user.id, text, reply_markup=markup)
    states_of_users[message.from_user.id]["STATE"] = "AMOUNT"
    states_of_users[message.from_user.id]["ADDRESS"] = message.text


@bot.message_handler(func=lambda message: states_of_users.get(message.from_user.id)["STATE"] == "AMOUNT")
def get_confirmation_of_transaction(message):
    if message.text == 'Меню':
        del states_of_users[message.from_user.id]
        menu(message)
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)
    if message.text.isdigit():
        text = f'Вы хотите перевести {message.text} сатоши, \n'\
               f'на биткоин адрес {states_of_users[message.from_user.id]["ADDRESS"]}: '
        confirm = telebot.types.KeyboardButton('Подтверждаю')
        markup.add(confirm)
        bot.send_message(message.chat.id, text, reply_markup=markup)
        states_of_users[message.from_user.id]["STATE"] = "CONFIRM"
        states_of_users[message.from_user.id]["AMOUNT"] = int(message.text)
    else:
        text = f'Вы ввели не число, попробуйте заново'
        bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(func=lambda message: states_of_users.get(message.from_user.id)["STATE"] == "CONFIRM")
def get_hash_of_transaction(message):
    if message.text == 'Меню':
        del states_of_users[message.from_user.id]
        menu(message)
    elif message.text == 'Подтверждаю':
        bot.send_message(
            message.chat.id,
            f'Ваша транзакция: ' + str(
                client.create_transaction(
                    message.from_user.id,
                    states_of_users[message.from_user.id]["ADDRESS"],
                    states_of_users[message.from_user.id]["AMOUNT"]
                )
            )
        )
        del states_of_users[message.from_user.id]
        menu(message)


bot.infinity_polling()
