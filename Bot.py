import telebot
from telebot import types

bot = telebot.TeleBot("8707431704:AAHP_r4My1E_L4D7PSdN4OSKn9pleV4ajqU")

# Хранилище очков и прогресса
users = {}

def get_user(uid):
    if uid not in users:
        users[uid] = {"name": "", "score": 0, "day": 0, "answers": []}
    return users[uid]

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    get_user(uid)
    bot.send_message(uid,
        "🕵️ Добро пожаловать в ООО «Рога и Копыта Диджитал»!\n"
        "Ты — новый сотрудник. В первый день тебе выдали ноутбук, "
        "доступ к почте и тревожную записку от уволенного сисадмина.\n\n"
        "Напиши своё имя, стажёр.")
    bot.register_next_step_handler(message, set_name)

def set_name(message):
    uid = message.from_user.id
    users[uid]["name"] = message.text
    bot.send_message(uid,
        f"Отлично, {message.text}. Начинаем день 1.\n"
        "Команды: /day1 /day2 /day3 /day4 /day5 /score /final")

@bot.message_handler(commands=['day1'])
def day1(message):
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("12345678", callback_data="d1_1_bad"),
        types.InlineKeyboardButton("Qwerty2026", callback_data="d1_1_mid"),
        types.InlineKeyboardButton("Zima!Kolbasa#Sneg2026", callback_data="d1_1_good"),
        types.InlineKeyboardButton("Сгенерировать в менеджере", callback_data="d1_1_good")
    )
    bot.send_message(uid,
        "📅 День 1. IT-отдел просит придумать пароль.\n"
        "Какой выберешь?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("d1_1_"))
def answer_d1_1(call):
    uid = call.from_user.id
    u = get_user(uid)
    if call.data == "d1_1_bad":
        u["score"] -= 5
        text = "❌ Это не пароль, это приглашение для брутфорса."
    elif call.data == "d1_1_mid":
        u["score"] += 3
        text = "⚠️ Лучше, но всё ещё в топ-100 словарях."
    else:
        u["score"] += 10
        text = "✅ Красиво! Мнемоника + менеджер паролей = база."
    bot.answer_callback_query(call.id)
    bot.send_message(uid, f"{text}\nТекущий счёт: {u['score']}")

@bot.message_handler(commands=['score'])
def score(message):
    u = get_user(message.from_user.id)
    bot.send_message(message.chat.id, f"💰 Очки: {u['score']}")

@bot.message_handler(commands=['final'])
def final(message):
    uid = message.from_user.id
    u = get_user(uid)
    s = u["score"]
    if s < 20:
        rank = "Стажёр, который уже слил пароль"
    elif s < 50:
        rank = "Бдительный пользователь"
    elif s < 80:
        rank = "Кибер-Джедай"
    else:
        rank = "Хранитель паролей, гроза фишеров"
    bot.send_message(uid, f"🏆 Итог: {s} очков.\nЗвание: {rank}")

bot.polling()