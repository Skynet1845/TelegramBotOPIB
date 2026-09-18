# -*- coding: utf-8 -*-
import telebot
from telebot import types
import json
import os
import time

# ============================================================
#  НАСТРОЙКИ
# ============================================================
BOT_TOKEN = "ВСТАВЬ_СЮДА_НОВЫЙ_ТОКЕН"
LEADERS_FILE = "leaders.json"

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище пользователей в памяти (сбрасывается при рестарте)
users = {}


# ============================================================
#  УТИЛИТЫ
# ============================================================

def load_leaders():
    if os.path.exists(LEADERS_FILE):
        try:
            with open(LEADERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_leaders(data):
    with open(LEADERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_leader(name, score):
    leaders = load_leaders()
    leaders.append({"name": name, "score": score})
    leaders.sort(key=lambda x: x["score"], reverse=True)
    save_leaders(leaders[:20])


def get_user(uid):
    if uid not in users:
        users[uid] = {
            "name": "Аноним",
            "score": 0,
            "day": 0,              # сколько дней завершено
            "hints": [],           # собранные пасхальные подсказки
            "mistakes": [],        # разбор ошибок
            "finished": False,
            "exam_step": 0,
            "exam_score": 0,
            "secret_resolved": False,
        }
    return users[uid]


def add_hint(uid, key):
    u = get_user(uid)
    if key not in u["hints"]:
        u["hints"].append(key)


def score_msg(uid, points, text, mistake=None):
    """Формирует ответ с изменением счёта."""
    u = get_user(uid)
    u["score"] = max(0, u["score"] + points)
    if mistake:
        u["mistakes"].append(mistake)
    sign = "+" if points > 0 else ""
    return f"{text}\n\n💰 {sign}{points} очк. Всего: <b>{u['score']}</b>"


def require_day(uid, day_num):
    """Пускает в день N, только если пройден N-1."""
    u = get_user(uid)
    if day_num > 1 and u["day"] < day_num - 1:
        bot.send_message(uid,
            f"⏳ Сначала закончи день {day_num - 1}. Команда /day{day_num - 1}.")
        return False
    return True


# ============================================================
#  СТАРТ И ОБЩИЕ КОМАНДЫ
# ============================================================

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    u = get_user(uid)
    if u["name"] != "Аноним" and (u["score"] > 0 or u["day"] > 0):
        bot.send_message(uid,
            f"С возвращением, <b>{u['name']}</b>!\n"
            f"Счёт: {u['score']} очк. День: {u['day']}. "
            f"Подсказок: {len(u['hints'])}.\n\n"
            "Команды: /day1 /day2 /day3 /day4 /day5 /exam /score /final /leaders /help",
            parse_mode="HTML")
        return
    bot.send_message(uid,
        "🕵️ <b>ООО «Рога и Копыта Диджитал»</b>\n\n"
        "Ты — новый сотрудник. В первый день выдали ноутбук, доступ к почте "
        "и тревожную записку от уволенного сисадмина:\n\n"
        "<i>«Они уже внутри. Не открывай вложения. "
        "И не говори с "Анной из бухгалтерии".»</i>\n\n"
        "Напиши своё имя, стажёр.",
        parse_mode="HTML")
    bot.register_next_step_handler(message, set_name)


def set_name(message):
    uid = message.from_user.id
    u = get_user(uid)
    u["name"] = message.text[:50]
    bot.send_message(uid,
        f"Отлично, <b>{u['name']}</b>. Начинаем стажировку.\n\n"
        "📚 Команды:\n"
        "/day1 — Пароли и аутентификация\n"
        "/day2 — Фишинг\n"
        "/day3 — Социальная инженерия\n"
        "/day4 — Флешки и файлы\n"
        "/day5 — Чистый стол\n"
        "/exam — Финальный экзамен\n"
        "/score — счёт\n"
        "/final — итог и звание\n"
        "/leaders — таблица лидеров\n"
        "/help — помощь\n\n"
        "<i>Совет: внимательно читай детали. Некоторые ответы открывают скрытые подсказки.</i>",
        parse_mode="HTML")


@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.from_user.id,
        "📖 <b>Как играть</b>\n\n"
        "Ты — стажёр. Проходи дни по порядку: /day1 → /day2 → /day3 → /day4 → /day5, "
        "потом /exam.\n\n"
        "За правильные ответы — очки, за опасные — минус. В конце — звание.\n\n"
        "<i>Совет: собирай скрытые подсказки (появятся при правильных ответах). "
        "После дня 5 попробуй команду /truth.</i>",
        parse_mode="HTML")


@bot.message_handler(commands=['score'])
def score_cmd(message):
    u = get_user(message.from_user.id)
    bot.send_message(message.chat.id,
        f"💰 Очки: <b>{u['score']}</b>\n"
        f"📅 Завершено дней: {u['day']}/5\n"
        f"🔍 Подсказок собрано: {len(u['hints'])}/3\n"
        f"❌ Ошибок: {len(u['mistakes'])}",
        parse_mode="HTML")


@bot.message_handler(commands=['reset'])
def reset_cmd(message):
    uid = message.from_user.id
    users[uid] = {
        "name": "Аноним", "score": 0, "day": 0,
        "hints": [], "mistakes": [], "finished": False,
        "exam_step": 0, "exam_score": 0, "secret_resolved": False,
    }
    bot.send_message(uid, "🔄 Прогресс сброшен. Жми /start.")


@bot.message_handler(commands=['leaders'])
def leaders_cmd(message):
    leaders = load_leaders()
    if not leaders:
        bot.send_message(message.chat.id, "📊 Таблица лидеров пока пуста.")
        return
    text = "🏆 <b>Таблица лидеров</b>\n\n"
    for i, l in enumerate(leaders[:10], 1):
        medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f" {i}."
        text += f"{medal} <b>{l['name']}</b> — {l['score']} очк.\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")


# ============================================================
#  ДЕНЬ 1 — ПАРОЛИ
# ============================================================

@bot.message_handler(commands=['day1'])
def day1(message):
    if not require_day(message.from_user.id, 1):
        return
    send_d1s1(message.from_user.id)


def send_d1s1(uid):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("12345678", callback_data="d1s1_bad"),
        types.InlineKeyboardButton("Qwerty2026", callback_data="d1s1_mid"),
        types.InlineKeyboardButton("Zima!Kolbasa#Sneg2026", callback_data="d1s1_good"),
        types.InlineKeyboardButton("Сгенерировать в менеджере паролей", callback_data="d1s1_man"),
    )
    bot.send_message(uid,
        "📅 <b>День 1. Вопрос 1/3.</b>\n\n"
        "IT-отдел просит придумать пароль для рабочего аккаунта.\n"
        "Какой выберешь?",
        parse_mode="HTML", reply_markup=m)


@bot.callback_query_handler(func=lambda c: c.data.startswith("d1s1_"))
def d1s1(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if call.data == "d1s1_bad":
        text = score_msg(uid, -5,
            "❌ <b>Это не пароль — приглашение для брутфорса.</b>\n"
            "12345678 взламывается за секунды. Проверить можно на howsecureismypassword.net.",
            mistake="Пароль 12345678")
    elif call.data == "d1s1_mid":
        text = score_msg(uid, 3,
            "⚠️ <b>Лучше, но всё ещё плохо.</b>\n"
            "Qwerty в топ-5 популярных. Год в конце ничего не меняет: брутфорс справится за минуты.",
            mistake="Пароль Qwerty2026")
    elif call.data == "d1s1_good":
        text = score_msg(uid, 10,
            "✅ <b>Отлично!</b> Мнемоника + спецсимволы + 20 знаков — то, что нужно.\n"
            "Пример: «Зимой колбасу ем со снегом» → Zima!Kolbasa#Sneg2026.")
    else:
        text = score_msg(uid, 10,
            "✅ <b>Менеджер паролей — золотой стандарт.</b>\n"
            "KeePassXC, Bitwarden, 1Password. Пароль, который ты не помнишь, — пароль, который не подберут.")
    bot.send_message(uid, text, parse_mode="HTML")
    time.sleep(0.4)
    send_d1s2(uid)


def send_d1s2(uid):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("Да, включу прямо сейчас", callback_data="d1s2_yes"),
        types.InlineKeyboardButton("Потом как-нибудь", callback_data="d1s2_later"),
        types.InlineKeyboardButton("А это не замедлит работу?", callback_data="d1s2_why"),
    )
    bot.send_message(uid,
        "🔐 <b>День 1. Вопрос 2/3.</b>\n\n"
        "IT-отдел настойчиво рекомендует включить MFA.\nЧто делаешь?",
        parse_mode="HTML", reply_markup=m)


@bot.callback_query_handler(func=lambda c: c.data.startswith("d1s2_"))
def d1s2(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if call.data == "d1s2_yes":
        text = score_msg(uid, 10,
            "✅ <b>Именно так.</b>\nMFA снижает риск взлома аккаунта на 99.9% (данные Microsoft).")
    elif call.data == "d1s2_later":
        text = score_msg(uid, -5,
            "❌ «Потом» в ИБ = «никогда». Большинство взломов — из-за отсутствия MFA.",
            mistake="Откладывание MFA")
    else:
        text = score_msg(uid, 3,
            "⚠️ <b>Вопрос нормальный, но ответ один — да.</b>\n"
            "MFA замедляет тебя на секунды. Взлом без MFA — на часы разбора с ИБ.",
            mistake="Сомнения насчёт MFA")
    bot.send_message(uid, text, parse_mode="HTML")
    time.sleep(0.4)
    send_d1s3(uid)


def send_d1s3(uid):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("Дать пароль", callback_data="d1s3_give"),
        types.InlineKeyboardButton("Отказать и помочь по-другому", callback_data="d1s3_refuse"),
        types.InlineKeyboardButton("Дать, а потом сменить", callback_data="d1s3_swap"),
    )
    bot.send_message(uid,
        "👥 <b>День 1. Вопрос 3/3.</b>\n\n"
        "Коллега просит: «Дай свой пароль, мне на 5 минут надо кое-что проверить».\n"
        "Твои действия?",
        parse_mode="HTML", reply_markup=m)


@bot.callback_query_handler(func=lambda c: c.data.startswith("d1s3_"))
def d1s3(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if call.data == "d1s3_give":
        text = score_msg(uid, -10,
            "❌ <b>Категорически нельзя.</b>\n"
            "Даже «на 5 минут». Пароль — персональный идентификатор. Всё, что сделают под ним, спишут на тебя.",
            mistake="Передача пароля коллеге")
    elif call.data == "d1s3_refuse":
        text = score_msg(uid, 10,
            "✅ <b>Верно.</b>\nЛучше помочь коллеге в его задаче, но не отдавать свой пароль.")
    else:
        text = score_msg(uid, 3,
            "⚠️ <b>Полумеры не работают.</b>\n"
            "Пока ты меняешь пароль, под твоей учёткой уже могли что-то сделать.",
            mistake="Пароль с последующей сменой")
    bot.send_message(uid, text, parse_mode="HTML")

    u = get_user(uid)
    u["day"] = max(u["day"], 1)
    time.sleep(0.5)
    bot.send_message(uid,
        "🏁 <b>День 1 завершён!</b>\nСледующий: /day2",
        parse_mode="HTML")


# ============================================================
#  ДЕНЬ 2 — ФИШИНГ
# ============================================================

@bot.message_handler(commands=['day2'])
def day2(message):
    if not require_day(message.from_user.id, 2):
        return
    send_d2p1(message.from_user.id)


def phishing_markup(prefix):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("✅ Безопасно", callback_data=f"{prefix}_safe"),
        types.InlineKeyboardButton("🎣 Фишинг", callback_data=f"{prefix}_phish"),
    )
    return m


def send_d2p1(uid):
    bot.send_message(uid,
        "📅 <b>День 2. Письмо 1/4.</b>\n\n"
        "<b>От:</b> hr@korporaciya-bonus.ru\n"
        "<b>Тема:</b> Вам начислена премия! Подтвердите данные карты\n"
        "<b>Вложение:</b> нет, ссылка внутри",
        parse_mode="HTML", reply_markup=phishing_markup("d2p1"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("d2p1_"))
def d2p1(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    u = get_user(uid)
    if call.data == "d2p1_phish":
        text = score_msg(uid, 10,
            "✅ <b>Верно. Это фишинг.</b>\n"
            "Чужой домен «korporaciya-bonus.ru», давление на жадность, "
            "ссылка на ввод данных карты. Классика.\n\n"
            "🔍 <i>В подписи мелькнул адрес: a.volkova@company-old.ru. "
            "Хм, а Анна из бухгалтерии уволилась три года назад...</i>")
        add_hint(uid, "volkova_old")
    else:
        text = score_msg(uid, -5,
            "❌ <b>Это фишинг.</b>\n"
            "Чужой домен, обещание премии, ввод данных карты — триггеры-близнецы.\n"
            "Запомни: HR никогда не просит данные карты по почте.",
            mistake="Пропустил фишинг с премией")
    bot.send_message(uid, text, parse_mode="HTML")
    time.sleep(0.4)
    send_d2p2(uid)


def send_d2p2(uid):
    bot.send_message(uid,
        "📩 <b>День 2. Письмо 2/4.</b>\n\n"
        "<b>От:</b> it-support@company.ru (домен с кириллической «о»)\n"
        "<b>Тема:</b> Обновите пароль по ссылке в течение часа\n"
        "<b>Вложение:</b> ссылка",
        parse_mode="HTML", reply_markup=phishing_markup("d2p2"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("d2p2_"))
def d2p2(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if call.data == "d2p2_phish":
        text = score_msg(uid, 10,
            "✅ <b>Верно.</b>\n"
            "Хитрость с кириллической «о» в домене — гомографная атака. "
            "Визуально не отличить от настоящего.")
    else:
        text = score_msg(uid, -5,
            "❌ <b>Это фишинг.</b>\n"
            "IT-отдел не просит менять пароль по ссылке из письма. "
            "Заходи в корпоративный портал вручную.",
            mistake="Кириллический домен не заметил")
    bot.send_message(uid, text, parse_mode="HTML")
    time.sleep(0.4)
    send_d2p3(uid)


def send_d2p3(uid):
    bot.send_message(uid,
        "📩 <b>День 2. Письмо 3/4.</b>\n\n"
        "<b>От:</b> colleague@company.ru\n"
        "<b>Тема:</b> Смотри, что нашёл, по смете\n"
        "<b>Вложение:</b> smeta_final.xlsx.exe",
        parse_mode="HTML", reply_markup=phishing_markup("d2p3"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("d2p3_"))
def d2p3(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if call.data == "d2p3_phish":
        text = score_msg(uid, 10,
            "✅ <b>Верно.</b>\n"
            "Двойное расширение .xlsx.exe — трюк, чтобы значок Excel "
            "спрятал исполняемый файл. Настоящий Excel — только .xlsx.")
    else:
        text = score_msg(uid, -5,
            "❌ <b>Это фишинг.</b>\n"
            "Файл smeta_final.xlsx.exe — исполняемый. Открытие = запуск вируса. "
            "Уточни у коллеги по телефону, отправлял ли он это.",
            mistake="Открытие .xlsx.exe")
    bot.send_message(uid, text, parse_mode="HTML")
    time.sleep(0.4)
    send_d2p4(uid)


def send_d2p4(uid):
    bot.send_message(uid,
        "📩 <b>День 2. Письмо 4/4.</b>\n\n"
        "<b>От:</b> director@company.ru\n"
        "<b>Тема:</b> Срочно! Оплати счёт поставщику, реквизиты в файле\n"
        "<b>Вложение:</b> rekvizity.pdf",
        parse_mode="HTML", reply_markup=phishing_markup("d2p4"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("d2p4_"))
def d2p4(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if call.data == "d2p4_phish":
        text = score_msg(uid, 10,
            "✅ <b>Верно. Это BEC-атака (Business Email Compromise).</b>\n"
            "Директор не просит деньги по почте. Проверяй по второму каналу: звонок, "
            "личная встреча, корпоративный мессенджер.")
    else:
        text = score_msg(uid, -5,
            "❌ <b>Это BEC-атака.</b>\n"
            "Срочность + крупная сумма + реквизиты в письме — триггеры. "
            "Всегда перепроверяй по другому каналу.",
            mistake="Пропустил BEC-атаку")
    bot.send_message(uid, text, parse_mode="HTML")

    u = get_user(uid)
    u["day"] = max(u["day"], 2)
    time.sleep(0.5)
    bot.send_message(uid,
        "🏁 <b>День 2 завершён!</b>\nСледующий: /day3",
        parse_mode="HTML")


# ============================================================
#  ДЕНЬ 3 — СОЦИАЛЬНАЯ ИНЖЕНЕРИЯ
# ============================================================

@bot.message_handler(commands=['day3'])
def day3(message):
    if not require_day(message.from_user.id, 3):
        return
    send_d3s1(message.from_user.id)


def send_d3s1(uid):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("Назвать код", callback_data="d3s1_yes"),
        types.InlineKeyboardButton("Отказать и повесить трубку", callback_data="d3s1_no"),
        types.InlineKeyboardButton("Спросить имя и перезвонить в банк", callback_data="d3s1_back"),
    )
    bot.send_message(uid,
        "📞 <b>День 3. Вопрос 1/2.</b>\n\n"
        "Звонок «из службы безопасности банка»: "
        "«Подтвердите операцию, назовите код из СМС».",
        parse_mode="HTML", reply_markup=m)


@bot.callback_query_handler(func=lambda c: c.data.startswith("d3s1_"))
def d3s1(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if call.data == "d3s1_yes":
        text = score_msg(uid, -10,
            "❌ <b>Никому и никогда.</b>\n"
            "Даже если «из банка». Банк не спрашивает код из СМС. Вообще. Никогда.",
            mistake="Сообщил код из СМС")
    elif call.data == "d3s1_no":
        text = score_msg(uid, 10,
            "✅ <b>Молодец!</b> Положил трубку — сохранил деньги.")
    else:
        text = score_msg(uid, 10,
            "✅ <b>Правильный ход.</b>\n"
            "Настоящий банк всегда можно проверить через официальный номер на карте.")
    bot.send_message(uid, text, parse_mode="HTML")
    time.sleep(0.4)
    send_d3s2(uid)


def send_d3s2(uid):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("Проверить через корпоративную почту/звонок", callback_data="d3s2_check"),
        types.InlineKeyboardButton("Скинуть базу клиентов", callback_data="d3s2_send"),
        types.InlineKeyboardButton("Проигнорировать", callback_data="d3s2_ignore"),
    )
    bot.send_message(uid,
        "💬 <b>День 3. Вопрос 2/2.</b>\n\n"
        "В мессенджер пишет «директор»: «Скинь базу клиентов, надо срочно».",
        parse_mode="HTML", reply_markup=m)


@bot.callback_query_handler(func=lambda c: c.data.startswith("d3s2_"))
def d3s2(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if call.data == "d3s2_check":
        text = score_msg(uid, 10,
            "✅ <b>Верно.</b>\n"
            "Проверь по второму каналу: корпоративная почта, звонок. "
            "Директор не просит базы в мессенджере.")
    elif call.data == "d3s2_send":
        text = score_msg(uid, -10,
            "❌ <b>Это утечка.</b>\n"
            "База клиентов — коммерческая тайна. Через мессенджер — никогда.",
            mistake="Отправка базы через мессенджер")
    else:
        text = score_msg(uid, 3,
            "⚠️ <b>Игнор — не худшее, но лучше сообщить в ИБ.</b>\n"
            "Коллеги должны знать о попытке атаки.",
            mistake="Проигнорировал подозрительное сообщение")
    bot.send_message(uid, text, parse_mode="HTML")

    u = get_user(uid)
    u["day"] = max(u["day"], 3)
    time.sleep(0.5)
    bot.send_message(uid,
        "🏁 <b>День 3 завершён!</b>\nСледующий: /day4",
        parse_mode="HTML")


# ============================================================
#  ДЕНЬ 4 — ФЛЕШКИ И ФАЙЛЫ
# ============================================================

@bot.message_handler(commands=['day4'])
def day4(message):
    if not require_day(message.from_user.id, 4):
        return
    send_d4s1(message.from_user.id)


def send_d4s1(uid):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("Вставить в свой компьютер", callback_data="d4s1_plug"),
        types.InlineKeyboardButton("Отдать в ИБ", callback_data="d4s1_ib"),
        types.InlineKeyboardButton("Забрать домой", callback_data="d4s1_home"),
        types.InlineKeyboardButton("Сфотографировать и сообщить в ИБ", callback_data="d4s1_photo"),
    )
    bot.send_message(uid,
        "🔌 <b>День 4. Вопрос 1/2.</b>\n\n"
        "Нашёл USB-флешку в холле. На ней стикер «В.С. 2024».",
        parse_mode="HTML", reply_markup=m)


@bot.callback_query_handler(func=lambda c: c.data.startswith("d4s1_"))
def d4s1(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if call.data == "d4s1_plug":
        text = score_msg(uid, -10,
            "❌ <b>Поздравляем, ты теперь часть ботнета.</b>\n"
            "USB-дроппинг — реальная техника. Заражение происходит мгновенно.",
            mistake="Вставил найденную флешку")
    elif call.data == "d4s1_ib":
        text = score_msg(uid, 10,
            "✅ <b>Правильно.</b> Флешку — в ИБ, ИБ разберётся.\n\n"
            "🔍 <i>При передаче ты рассмотрел стикер: «В.С. 2024». "
            "Инициалы кажутся знакомыми...</i>")
        add_hint(uid, "vs_sticker")
    elif call.data == "d4s1_home":
        text = score_msg(uid, -10,
            "❌ <b>Дома тоже не стоит.</b>\n"
            "Это не трофей, это потенциальный носитель с эксплойтом.",
            mistake="Унёс флешку домой")
    else:
        text = score_msg(uid, 10,
            "✅ <b>Хорошо: фотофиксация + передача в ИБ.</b>\n\n"
            "🔍 <i>На фото видно: «В.С. 2024». Где-то ты эти инициалы уже видел...</i>")
        add_hint(uid, "vs_sticker")
    bot.send_message(uid, text, parse_mode="HTML")
    time.sleep(0.4)
    send_d4s2(uid)


def send_d4s2(uid):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("Обычной почтой", callback_data="d4s2_email"),
        types.InlineKeyboardButton("Через корпоративный файлообменник с паролем", callback_data="d4s2_share"),
        types.InlineKeyboardButton("Через личный Telegram", callback_data="d4s2_tg"),
    )
    bot.send_message(uid,
        "📤 <b>День 4. Вопрос 2/2.</b>\n\n"
        "Нужно передать конфиденциальный файл партнёру. Как?",
        parse_mode="HTML", reply_markup=m)


@bot.callback_query_handler(func=lambda c: c.data.startswith("d4s2_"))
def d4s2(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if call.data == "d4s2_email":
        text = score_msg(uid, 3,
            "⚠️ <b>Обычная почта без шифрования — не лучший выбор для коммерческой тайны.</b>",
            mistake="Отправка файла обычной почтой")
    elif call.data == "d4s2_share":
        text = score_msg(uid, 10,
            "✅ <b>Верно.</b> Корпоративный файлообменник с паролем и сроком действия — стандарт.")
    else:
        text = score_msg(uid, -5,
            "❌ <b>Личные мессенджеры — не для работы.</b>\n"
            "Файл уходит на чужие серверы. Утечка — вопрос времени.",
            mistake="Отправка файла через личный мессенджер")
    bot.send_message(uid, text, parse_mode="HTML")

    u = get_user(uid)
    u["day"] = max(u["day"], 4)
    time.sleep(0.5)
    bot.send_message(uid,
        "🏁 <b>День 4 завершён!</b>\nСледующий: /day5",
        parse_mode="HTML")


# ============================================================
#  ДЕНЬ 5 — ЧИСТЫЙ СТОЛ
# ============================================================

@bot.message_handler(commands=['day5'])
def day5(message):
    if not require_day(message.from_user.id, 5):
        return
    send_d5s1(message.from_user.id)


def send_d5s1(uid):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("Оставить как есть", callback_data="d5s1_leave"),
        types.InlineKeyboardButton("Убрать в сейф / ящик с замком", callback_data="d5s1_safe"),
        types.InlineKeyboardButton("Перевернуть листами вниз", callback_data="d5s1_flip"),
    )
    bot.send_message(uid,
        "🍽 <b>День 5. Вопрос 1/2.</b>\n\n"
        "Уходишь на обед. На столе лежит договор с клиентом. "
        "На папке видны инициалы «В.С.»",
        parse_mode="HTML", reply_markup=m)


@bot.callback_query_handler(func=lambda c: c.data.startswith("d5s1_"))
def d5s1(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if call.data == "d5s1_leave":
        text = score_msg(uid, -5,
            "❌ <b>Правило чистого стола:</b> уходя, убери всё конфиденциальное.",
            mistake="Оставил документ на столе")
    elif call.data == "d5s1_safe":
        text = score_msg(uid, 10,
            "✅ <b>Именно так.</b> В сейф или ящик с замком.\n\n"
            "🔍 <i>Инициалы «В.С.» на папке. Где-то ты их уже видел...</i>")
        add_hint(uid, "vs_folder")
    else:
        text = score_msg(uid, 3,
            "⚠️ <b>«Перевернуть» — это как закрыть глаза и надеяться, что тебя не видно.</b>\n"
            "Первые страницы всё ещё можно прочитать.",
            mistake="Перевернул документ")
        add_hint(uid, "vs_folder")
    bot.send_message(uid, text, parse_mode="HTML")
    time.sleep(0.4)
    send_d5s2(uid)


def send_d5s2(uid):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("Поддержать разговор", callback_data="d5s2_talk"),
        types.InlineKeyboardButton("Промолчать, потом напомнить о правилах", callback_data="d5s2_silent"),
        types.InlineKeyboardButton("Посмеяться и забыть", callback_data="d5s2_laugh"),
    )
    bot.send_message(uid,
        "🛗 <b>День 5. Вопрос 2/2.</b>\n\n"
        "В лифте коллеги обсуждают детали тендера. Ты — участник проекта.",
        parse_mode="HTML", reply_markup=m)


@bot.callback_query_handler(func=lambda c: c.data.startswith("d5s2_"))
def d5s2(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if call.data == "d5s2_talk":
        text = score_msg(uid, -5,
            "❌ <b>Обсуждение рабочих тем в публичных местах — утечка.</b>\n"
            "В лифте могут быть сотрудники других компаний.",
            mistake="Обсуждение тендера в лифте")
    elif call.data == "d5s2_silent":
        text = score_msg(uid, 10,
            "✅ <b>Молчать и потом напомнить коллегам о правилах — лучшее.</b>")
    else:
        text = score_msg(uid, 3,
            "⚠️ <b>Смех смехом, а тендер уплывёт к конкурентам.</b>\n"
            "Не критично, но культуру безопасности так не построить.",
            mistake="Не отреагировал на утечку в лифте")
    bot.send_message(uid, text, parse_mode="HTML")

    u = get_user(uid)
    u["day"] = max(u["day"], 5)
    time.sleep(0.5)
    bot.send_message(uid,
        "🏁 <b>День 5 завершён!</b>\n\n"
        "Остался финальный экзамен: /exam\n"
        "Или можешь попробовать /truth — если чувствуешь, что что-то не так.",
        parse_mode="HTML")


# ============================================================
#  ФИНАЛЬНЫЙ ЭКЗАМЕН
# ============================================================

EXAM = [
    {
        "q": "Что такое фишинг?",
        "opts": [
            ("Рыбалка в корпоративном пруду", "a"),
            ("Мошенничество с целью выманить данные", "b"),
            ("Способ сжатия файлов", "c"),
        ],
        "correct": "b",
        "why": "Фишинг — социальная инженерия через поддельные письма/сайты.",
    },
    {
        "q": "Что такое MFA?",
        "opts": [
            ("Модный формат файла", "a"),
            ("Многофакторная аутентификация", "b"),
            ("Министерство финансов", "c"),
        ],
        "correct": "b",
        "why": "MFA — подтверждение личности двумя и более способами.",
    },
    {
        "q": "Правило «чистого стола» означает:",
        "opts": [
            ("Протирать стол каждый час", "a"),
            ("Не оставлять конфиденциальные документы на виду", "b"),
            ("Есть только за рабочим столом", "c"),
        ],
        "correct": "b",
        "why": "Уходя с рабочего места — прячь всё конфиденциальное.",
    },
    {
        "q": "Вы ввели пароль на фишинговом сайте. Первое действие?",
        "opts": [
            ("Никому не говорить", "a"),
            ("Сменить пароль и сообщить в ИБ", "b"),
            ("Удалить письмо", "c"),
        ],
        "correct": "b",
        "why": "Смена пароля + уведомление ИБ минимизируют ущерб.",
    },
    {
        "q": "Нашли флешку в холле. Что делать?",
        "opts": [
            ("Вставить в рабочий компьютер", "a"),
            ("Отдать в ИБ", "b"),
            ("Забрать домой", "c"),
        ],
        "correct": "b",
        "why": "USB-дроппинг — реальная техника. Флешку — только в ИБ.",
    },
]


@bot.message_handler(commands=['exam'])
def exam_start(message):
    uid = message.from_user.id
    u = get_user(uid)
    if u["day"] < 5:
        bot.send_message(uid, "⏳ Сначала пройди все 5 дней.")
        return
    u["exam_step"] = 0
    u["exam_score"] = 0
    send_exam_question(uid)


def send_exam_question(uid):
    u = get_user(uid)
    step = u["exam_step"]
    if step >= len(EXAM):
        finish_exam(uid)
        return
    q = EXAM[step]
    m = types.InlineKeyboardMarkup(row_width=1)
    for text, key in q["opts"]:
        m.add(types.InlineKeyboardButton(text, callback_data=f"exam_{step}_{key}"))
    bot.send_message(uid,
        f"🎓 <b>Экзамен. Вопрос {step + 1}/{len(EXAM)}</b>\n\n{q['q']}",
        parse_mode="HTML", reply_markup=m)


@bot.callback_query_handler(func=lambda c: c.data.startswith("exam_"))
def exam_answer(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    parts = call.data.split("_")
    step = int(parts[1])
    key = parts[2]
    q = EXAM[step]
    u = get_user(uid)
    if key == q["correct"]:
        u["exam_score"] += 10
        u["score"] += 10
        text = f"✅ Верно! +10 очк.\n<i>{q['why']}</i>"
    else:
        u["mistakes"].append(f"Экзамен: {q['q']}")
        text = f"❌ Неверно. Правильный ответ: <b>{q['correct'].upper()}</b>.\n<i>{q['why']}</i>"
    bot.send_message(uid, text, parse_mode="HTML")
    u["exam_step"] += 1
    time.sleep(0.6)
    send_exam_question(uid)


def finish_exam(uid):
    u = get_user(uid)
    bot.send_message(uid,
        f"🎓 <b>Экзамен завершён!</b>\n\n"
        f"Правильных ответов: <b>{u['exam_score'] // 10}/{len(EXAM)}</b>\n"
        f"Общий счёт: <b>{u['score']}</b>\n\n"
        "Жми /final для получения звания.",
        parse_mode="HTML")


# ============================================================
#  ФИНАЛ И ЗВАНИЯ
# ============================================================

@bot.message_handler(commands=['final'])
def final_cmd(message):
    uid = message.from_user.id
    u = get_user(uid)
    s = u["score"]
    if s < 40:
        rank = "🥚 Стажёр, который уже слил пароль"
    elif s < 90:
        rank = "🙂 Бдительный пользователь"
    elif s < 140:
        rank = "🥷 Кибер-Джедай"
    else:
        rank = "🐉 Хранитель паролей, гроза фишеров"

    text = f"🏆 <b>Итог стажировки</b>\n\nОчки: <b>{s}</b>\nЗвание: {rank}\n\n"
    if u["mistakes"]:
        text += "<b>Работа над ошибками:</b>\n"
        for m in u["mistakes"][:6]:
            text += f"• {m}\n"
    else:
        text += "✨ Ни одной ошибки! Впечатляет.\n"

    if not u["finished"]:
        u["finished"] = True
        add_leader(u["name"], s)
        text += "\n📊 Ты в таблице лидеров: /leaders"

    if len(u["hints"]) >= 2:
        text += ("\n\n🔍 У тебя накопились странные подсказки: "
                 "старый адрес Анны, инициалы «В.С.»... "
                 "Попробуй /truth — если осмелишься.")

    bot.send_message(uid, text, parse_mode="HTML")


# ============================================================
#  ПАСХАЛКА — СЕКРЕТНАЯ КОНЦОВКА
# ============================================================

@bot.message_handler(commands=['truth'])
def truth_cmd(message):
    uid = message.from_user.id
    u = get_user(uid)
    if u["day"] < 5:
        bot.send_message(uid, "🤔 Рано. Сначала пройди стажировку до дня 5.")
        return
    if len(u["hints"]) < 2:
        bot.send_message(uid,
            "🤔 Ты чувствуешь, что здесь что-то не так, но данных мало.\n\n"
            f"🔍 Собрано подсказок: {len(u['hints'])}/3. "
            "Перепройди дни внимательно — детали решают всё.",
            parse_mode="HTML")
        return
    if u["secret_resolved"]:
        bot.send_message(uid, "Ты уже знаешь правду. /report или /silent — твой выбор.")
        return

    text = (
        "🔓 <b>Секретная концовка</b>\n\n"
        "Ты сопоставил детали:\n"
        "• Старый адрес <code>a.volkova@company-old.ru</code> из фишингового письма.\n"
        "• Инициалы «В.С.» на флешке и папке.\n"
        "• Записка уволенного сисадмина с предупреждением про «Анну из бухгалтерии».\n\n"
        "<b>Правда:</b> уволенный сисадмин — <b>Виктор Сергеевич Соколов</b>. "
        "Его уволили «за утечку», но настоящий виновник — <b>Анна Волкова</b>, "
        "чей старый аккаунт до сих пор активен и рассылает фишинг изнутри компании. "
        "Виктор оставил подсказки (инициалы В.С.) — чтобы кто-то догадался и нашёл правду.\n\n"
        "<b>Что будешь делать?</b>\n"
        "• /report — сообщить в СБ (+20 очк.)\n"
        "• /silent — промолчать (+5 очк.)"
    )
    bot.send_message(uid, text, parse_mode="HTML")


@bot.message_handler(commands=['report'])
def report_cmd(message):
    uid = message.from_user.id
    u = get_user(uid)
    if len(u["hints"]) < 2:
        bot.send_message(uid, "🤔 Тебе пока нечего сообщать.")
        return
    if u["secret_resolved"]:
        bot.send_message(uid, "Ты уже сделал выбор.")
        return
    u["secret_resolved"] = True
    u["score"] += 20
    add_leader(u["name"] + " (разоблачитель)", u["score"])
    bot.send_message(uid,
        "🕵️ <b>Ты сообщил в СБ.</b>\n\n"
        "Виктор оправдан. Анна задержана. Компания благодарит тебя.\n\n"
        "⭐ +20 очк. Итог: " + str(u["score"]) + ".\n"
        "Финальное звание: <b>Разоблачитель</b>.",
        parse_mode="HTML")


@bot.message_handler(commands=['silent'])
def silent_cmd(message):
    uid = message.from_user.id
    u = get_user(uid)
    if len(u["hints"]) < 2:
        bot.send_message(uid, "🤔 Тебе пока нечего скрывать.")
        return
    if u["secret_resolved"]:
        bot.send_message(uid, "Ты уже сделал выбор.")
        return
    u["secret_resolved"] = True
    u["score"] += 5
    add_leader(u["name"] + " (молчун)", u["score"])
    bot.send_message(uid,
        "🤐 <b>Ты промолчал.</b>\n\n"
        "Анна продолжает работать. Кто знает, чем это обернётся...\n\n"
        "⭐ +5 очк. Итог: " + str(u["score"]) + ".\n"
        "Финальное звание: <b>Осторожный наблюдатель</b>.",
        parse_mode="HTML")


# ============================================================
#  ЗАПУСК С АВТОПЕРЕПОДКЛЮЧЕНИЕМ 
# ============================================================

if __name__ == "__main__":
    print("Бот запущен. Ctrl+C для остановки.")
    while True:
        try:
            bot.polling(none_stop=True, timeout=30, long_polling_timeout=20)
        except Exception as e:
            print(f"[!] Ошибка polling: {e}. Перезапуск через 5 сек...")
            time.sleep(5)