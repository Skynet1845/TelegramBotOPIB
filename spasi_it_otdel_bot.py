
import json
import os
import threading

import telebot
from telebot import types


# ============================================================
# НАСТРОЙКИ
# ============================================================

TOKEN = os.getenv("BOT_TOKEN", "").strip()
DATA_FILE = "users.json"

if not TOKEN:
    raise RuntimeError(
        "Не найден токен бота. Перед запуском задай переменную окружения BOT_TOKEN."
    )

bot = telebot.TeleBot(TOKEN)
data_lock = threading.RLock()


# ============================================================
# СЦЕНАРИИ
# ============================================================

DAYS = {
    1: {
        "title": "Добро пожаловать, или Пароль от всего",
        "questions": [
            {
                "id": "d1_q1",
                "topic": "Пароли",
                "text": (
                    "Ситуация 1 из 3.\n\n"
                    "IT-отдел просит придумать пароль для корпоративной учётной записи.\n"
                    "Какой вариант выберешь?"
                ),
                "options": [
                    {
                        "text": "12345678",
                        "points": -5,
                        "feedback": "❌ Это не пароль, это приглашение для перебора."
                    },
                    {
                        "text": "Qwerty2026",
                        "points": 3,
                        "feedback": "⚠️ Лучше, но шаблон слишком предсказуем и встречается в словарях."
                    },
                    {
                        "text": "Zima!Kolbasa#Sneg2026",
                        "points": 10,
                        "feedback": "✅ Хорошо: длинная запоминаемая парольная фраза заметно надёжнее."
                    },
                    {
                        "text": "Сгенерировать в менеджере паролей",
                        "points": 10,
                        "feedback": "✅ Отлично: менеджер может создать длинный уникальный пароль."
                    },
                ],
            },
            {
                "id": "d1_q2",
                "topic": "MFA",
                "text": (
                    "Ситуация 2 из 3.\n\n"
                    "Система предлагает включить многофакторную аутентификацию (MFA).\n"
                    "Что ответишь?"
                ),
                "options": [
                    {
                        "text": "Да, конечно",
                        "points": 10,
                        "feedback": "✅ Верно. MFA заметно снижает риск захвата аккаунта при утечке пароля."
                    },
                    {
                        "text": "Потом",
                        "points": -5,
                        "feedback": "❌ Откладывать защиту — значит оставлять аккаунт уязвимым."
                    },
                    {
                        "text": "А это не замедлит работу?",
                        "points": 3,
                        "feedback": "⚠️ Вопрос разумный, но безопасность важнее пары дополнительных секунд при входе."
                    },
                ],
            },
            {
                "id": "d1_q3",
                "topic": "Пароли",
                "text": (
                    "Ситуация 3 из 3.\n\n"
                    "Коллега просит твой пароль «буквально на 5 минут», чтобы срочно проверить документ.\n"
                    "Что сделаешь?"
                ),
                "options": [
                    {
                        "text": "Дать пароль",
                        "points": -10,
                        "feedback": "❌ Пароль нельзя передавать другим людям, даже коллегам."
                    },
                    {
                        "text": "Отказать и предложить помощь",
                        "points": 10,
                        "feedback": "✅ Правильно. Помочь можно без передачи своих учётных данных."
                    },
                    {
                        "text": "Дать, но потом сменить",
                        "points": 3,
                        "feedback": "⚠️ Смена пароля потом не отменяет риск действий от твоего имени сейчас."
                    },
                ],
            },
        ],
    },
    2: {
        "title": "Фишинг-тир",
        "questions": [
            {
                "id": "d2_q1",
                "topic": "Фишинг",
                "text": (
                    "Письмо 1 из 4.\n\n"
                    "От: hr@korporaciya-bonus.ru\n"
                    "Тема: «Вам начислена премия!»\n\n"
                    "В письме просят перейти по ссылке и ввести данные банковской карты."
                ),
                "options": [
                    {
                        "text": "Открыть ссылку и ввести данные",
                        "points": -10,
                        "feedback": "❌ Классический фишинг: чужой домен и приманка деньгами."
                    },
                    {
                        "text": "Просто удалить письмо",
                        "points": 3,
                        "feedback": "⚠️ Удалить безопаснее, чем открыть, но лучше ещё сообщить об атаке."
                    },
                    {
                        "text": "Удалить и сообщить в ИБ",
                        "points": 10,
                        "feedback": "✅ Верно. Не взаимодействуем с письмом и предупреждаем ИБ."
                    },
                ],
            },
            {
                "id": "d2_q2",
                "topic": "Фишинг",
                "text": (
                    "Письмо 2 из 4.\n\n"
                    "От: it-support@company.ru\n"
                    "Тема: «Срочно обновите пароль»\n\n"
                    "В письме есть ссылка на страницу смены пароля."
                ),
                "options": [
                    {
                        "text": "Сразу перейти по ссылке",
                        "points": -5,
                        "feedback": "❌ Даже знакомый адрес отправителя не гарантирует безопасность ссылки."
                    },
                    {
                        "text": "Проверить домен и уточнить у IT/ИБ",
                        "points": 10,
                        "feedback": "✅ Правильно. Лучше проверить запрос по независимому официальному каналу."
                    },
                    {
                        "text": "Удалить не читая",
                        "points": 3,
                        "feedback": "⚠️ Это безопаснее перехода по ссылке, но можно пропустить реальное уведомление."
                    },
                ],
            },
            {
                "id": "d2_q3",
                "topic": "Вложения",
                "text": (
                    "Письмо 3 из 4.\n\n"
                    "Письмо пришло от реального коллеги.\n"
                    "Вложение: смета.xlsx.exe\n\n"
                    "Что делать?"
                ),
                "options": [
                    {
                        "text": "Открыть: коллега же настоящий",
                        "points": -10,
                        "feedback": "❌ Учётная запись коллеги могла быть взломана, а .exe — исполняемый файл."
                    },
                    {
                        "text": "Не открывать и уточнить у коллеги по телефону",
                        "points": 10,
                        "feedback": "✅ Верно. Проверяем отправителя по другому каналу до открытия вложения."
                    },
                    {
                        "text": "Переслать знакомому, пусть проверит",
                        "points": -5,
                        "feedback": "❌ Так можно распространить вредоносный файл дальше."
                    },
                ],
            },
            {
                "id": "d2_q4",
                "topic": "BEC и социнженерия",
                "text": (
                    "Письмо 4 из 4.\n\n"
                    "От: director@company.ru\n"
                    "Тема: «Срочно!»\n\n"
                    "«Переведи 50 000 ₽ на этот счёт. Я на встрече, не звони»."
                ),
                "options": [
                    {
                        "text": "Сразу перевести",
                        "points": -10,
                        "feedback": "❌ Срочность и запрет на проверку — признаки BEC/социальной инженерии."
                    },
                    {
                        "text": "Проверить запрос по другому каналу",
                        "points": 10,
                        "feedback": "✅ Верно. Финансовые запросы нужно подтверждать независимо."
                    },
                    {
                        "text": "Перевести сначала небольшую сумму",
                        "points": -5,
                        "feedback": "❌ Размер суммы не делает мошеннический запрос безопасным."
                    },
                ],
            },
        ],
    },
    3: {
        "title": "Звонок другу",
        "questions": [
            {
                "id": "d3_q1",
                "topic": "Социальная инженерия",
                "text": (
                    "Ситуация 1 из 2.\n\n"
                    "Звонят «из техподдержки банка»:\n"
                    "«Для отмены подозрительной операции назовите код из СМС»."
                ),
                "options": [
                    {
                        "text": "Назвать код",
                        "points": -10,
                        "feedback": "❌ Коды подтверждения нельзя сообщать по телефону."
                    },
                    {
                        "text": "Отказать и положить трубку",
                        "points": 10,
                        "feedback": "✅ Правильно. После этого лучше самостоятельно связаться с банком."
                    },
                    {
                        "text": "Спросить имя и перезвонить в банк",
                        "points": 10,
                        "feedback": "✅ Отлично. Используй официальный номер банка, а не номер звонящего."
                    },
                    {
                        "text": "Назвать не все цифры",
                        "points": -5,
                        "feedback": "❌ Это как наполовину прыгнуть в пропасть: код всё равно нельзя раскрывать."
                    },
                ],
            },
            {
                "id": "d3_q2",
                "topic": "BEC и социнженерия",
                "text": (
                    "Ситуация 2 из 2.\n\n"
                    "В мессенджере пишет «директор» и просит срочно отправить базу клиентов.\n"
                    "Аватар и имя похожи на настоящие."
                ),
                "options": [
                    {
                        "text": "Отправить базу",
                        "points": -10,
                        "feedback": "❌ Имя и аватар легко подделать. Так можно устроить утечку данных."
                    },
                    {
                        "text": "Проверить запрос по официальному каналу",
                        "points": 10,
                        "feedback": "✅ Верно. Для чувствительных данных нужна независимая проверка личности."
                    },
                    {
                        "text": "Попросить подтверждение в том же чате",
                        "points": 3,
                        "feedback": "⚠️ Если аккаунт поддельный или взломан, подтверждение в том же канале ничего не докажет."
                    },
                ],
            },
        ],
    },
    4: {
        "title": "Флешка из ниоткуда",
        "questions": [
            {
                "id": "d4_q1",
                "topic": "Съёмные носители",
                "text": (
                    "Ситуация 1 из 2.\n\n"
                    "В холле офиса лежит неизвестная USB-флешка.\n"
                    "Что сделаешь?"
                ),
                "options": [
                    {
                        "text": "Вставить в рабочий компьютер",
                        "points": -10,
                        "feedback": "❌ Неизвестный USB-носитель может содержать вредоносный код."
                    },
                    {
                        "text": "Передать флешку в ИБ",
                        "points": 10,
                        "feedback": "✅ Правильно. Пусть носитель проверяют специалисты в безопасной среде."
                    },
                    {
                        "text": "Забрать домой",
                        "points": -10,
                        "feedback": "❌ Риск просто переносится на домашнее устройство и сеть."
                    },
                    {
                        "text": "Сфотографировать и сообщить в ИБ",
                        "points": 10,
                        "feedback": "✅ Безопасно: не подключаем носитель и уведомляем ответственных."
                    },
                ],
            },
            {
                "id": "d4_q2",
                "topic": "Передача данных",
                "text": (
                    "Ситуация 2 из 2.\n\n"
                    "Нужно передать партнёру рабочий файл с чувствительной информацией.\n"
                    "Как поступишь?"
                ),
                "options": [
                    {
                        "text": "Отправить обычной почтой без защиты",
                        "points": -5,
                        "feedback": "❌ Для чувствительных файлов нужен утверждённый защищённый канал."
                    },
                    {
                        "text": "Корпоративный файлообменник с защитой доступа",
                        "points": 10,
                        "feedback": "✅ Верно. Используем корпоративный защищённый инструмент и контроль доступа."
                    },
                    {
                        "text": "Отправить через личный Telegram",
                        "points": -5,
                        "feedback": "❌ Рабочие данные не стоит переносить в неутверждённые личные каналы."
                    },
                ],
            },
        ],
    },
    5: {
        "title": "Чистый стол и чистые руки",
        "questions": [
            {
                "id": "d5_q1",
                "topic": "Физическая безопасность",
                "text": (
                    "Ситуация 1 из 2.\n\n"
                    "Ты уходишь на обед. На столе лежит договор с клиентом.\n"
                    "Что делать?"
                ),
                "options": [
                    {
                        "text": "Оставить на столе",
                        "points": -5,
                        "feedback": "❌ Документ может увидеть или забрать посторонний."
                    },
                    {
                        "text": "Убрать в запираемый ящик/шкаф",
                        "points": 10,
                        "feedback": "✅ Верно. Правило чистого стола снижает риск утечки."
                    },
                    {
                        "text": "Просто перевернуть листы",
                        "points": 3,
                        "feedback": "⚠️ Лучше, чем ничего, но это не защищает документ от доступа."
                    },
                ],
            },
            {
                "id": "d5_q2",
                "topic": "Конфиденциальность",
                "text": (
                    "Ситуация 2 из 2.\n\n"
                    "В лифте коллеги обсуждают детали закрытого тендера. Ты участвуешь в проекте.\n"
                    "Что сделаешь?"
                ),
                "options": [
                    {
                        "text": "Поддержать разговор",
                        "points": -5,
                        "feedback": "❌ Общедоступное место — плохое место для обсуждения конфиденциальных деталей."
                    },
                    {
                        "text": "Не обсуждать и позже напомнить о правилах",
                        "points": 10,
                        "feedback": "✅ Верно. Чувствительную информацию обсуждают только в подходящей обстановке."
                    },
                ],
            },
        ],
    },
}


EXAM = [
    {
        "id": "exam_q1",
        "topic": "MFA",
        "text": (
            "Экзамен 1 из 5.\n\n"
            "На телефоне внезапно появляется запрос MFA на вход, который ты не инициировал."
        ),
        "options": [
            {"text": "Подтвердить, вдруг это IT", "points": -10},
            {"text": "Отклонить и сообщить в ИБ", "points": 10},
            {"text": "Просто игнорировать", "points": 3},
        ],
    },
    {
        "id": "exam_q2",
        "topic": "Фишинг",
        "text": (
            "Экзамен 2 из 5.\n\n"
            "Приходит письмо со ссылкой на «корпоративный портал». "
            "Адрес ссылки выглядит как company-security-login.com."
        ),
        "options": [
            {"text": "Войти по ссылке", "points": -10},
            {"text": "Самостоятельно открыть известный корпоративный портал и сообщить о письме", "points": 10},
            {"text": "Переслать коллеге и спросить, работает ли ссылка", "points": -5},
        ],
    },
    {
        "id": "exam_q3",
        "topic": "Вложения",
        "text": (
            "Экзамен 3 из 5.\n\n"
            "Коллега прислал файл report.pdf.exe и пишет: «Срочно открой»."
        ),
        "options": [
            {"text": "Открыть", "points": -10},
            {"text": "Не открывать и проверить отправителя по другому каналу", "points": 10},
            {"text": "Переименовать в report.pdf и открыть", "points": -5},
        ],
    },
    {
        "id": "exam_q4",
        "topic": "Пароли",
        "text": (
            "Экзамен 4 из 5.\n\n"
            "У тебя 15 рабочих сервисов. Как лучше организовать пароли?"
        ),
        "options": [
            {"text": "Один сложный пароль на все сервисы", "points": -5},
            {"text": "Уникальные пароли в менеджере паролей", "points": 10},
            {"text": "Записать все пароли в заметку на рабочем столе", "points": -10},
        ],
    },
    {
        "id": "exam_q5",
        "topic": "BEC и социнженерия",
        "text": (
            "Экзамен 5 из 5.\n\n"
            "«Директор» просит в мессенджере срочно оплатить новый счёт и пишет, что звонить ему нельзя."
        ),
        "options": [
            {"text": "Оплатить: просьба срочная", "points": -10},
            {"text": "Проверить запрос по независимому официальному каналу", "points": 10},
            {"text": "Попросить повторить просьбу в том же чате", "points": 3},
        ],
    },
]


TOPIC_ADVICE = {
    "Пароли": "используй уникальные длинные пароли и менеджер паролей; не передавай пароль другим.",
    "MFA": "включай MFA и никогда не подтверждай неожиданные запросы на вход.",
    "Фишинг": "проверяй домен, ссылки и контекст письма; сомнительные сообщения передавай в ИБ.",
    "Вложения": "не открывай неожиданные исполняемые файлы и проверяй отправителя по другому каналу.",
    "BEC и социнженерия": "срочные просьбы о деньгах или данных подтверждай по независимому официальному каналу.",
    "Социальная инженерия": "не сообщай коды из СМС и не доверяй личности звонящего без проверки.",
    "Съёмные носители": "не подключай неизвестные USB-устройства к рабочим или личным компьютерам.",
    "Передача данных": "используй только утверждённые корпоративные каналы и контроль доступа.",
    "Физическая безопасность": "не оставляй документы и устройства без присмотра; соблюдай правило чистого стола.",
    "Конфиденциальность": "не обсуждай чувствительные рабочие данные в общественных местах.",
}


# ============================================================
# ПОДСЧЁТ МАКСИМАЛЬНОГО БАЛЛА
# ============================================================

def question_max(question):
    return max(option["points"] for option in question["options"])


MAX_SCORE = (
    sum(
        question_max(question)
        for day in DAYS.values()
        for question in day["questions"]
    )
    + sum(question_max(question) for question in EXAM)
)


# ============================================================
# ХРАНЕНИЕ ДАННЫХ
# ============================================================

def default_user():
    return {
        "name": "",
        "score": 0,
        "answered": {},
        "completed_days": [],
        "awaiting_name": False,
    }


def normalize_user(user):
    base = default_user()
    if isinstance(user, dict):
        base.update(user)

    if not isinstance(base.get("answered"), dict):
        base["answered"] = {}

    if not isinstance(base.get("completed_days"), list):
        base["completed_days"] = []

    return base


def load_users():
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            raw = json.load(file)

        return {
            str(uid): normalize_user(user)
            for uid, user in raw.items()
        }
    except (OSError, json.JSONDecodeError):
        return {}


users = load_users()


def save_users():
    with data_lock:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(users, file, ensure_ascii=False, indent=2)


def get_user(uid):
    key = str(uid)

    with data_lock:
        if key not in users:
            users[key] = default_user()
            save_users()

        users[key] = normalize_user(users[key])
        return users[key]


# ============================================================
# СЛУЖЕБНЫЕ ФУНКЦИИ
# ============================================================

def is_registered(uid):
    return bool(get_user(uid)["name"])


def require_registration(message):
    if not is_registered(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "Сначала зарегистрируйся: отправь /start и введи своё имя."
        )
        return False
    return True


def make_keyboard(prefix, question):
    markup = types.InlineKeyboardMarkup(row_width=1)

    for index, option in enumerate(question["options"]):
        markup.add(
            types.InlineKeyboardButton(
                option["text"],
                callback_data=f"{prefix}:{index}"
            )
        )

    return markup


def remove_keyboard(call):
    try:
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
    except Exception:
        pass


def all_previous_days_completed(user, day_number):
    return all(
        day in user["completed_days"]
        for day in range(1, day_number)
    )


def next_unanswered_day_question(user, day_number):
    for index, question in enumerate(DAYS[day_number]["questions"]):
        if question["id"] not in user["answered"]:
            return index
    return None


def next_unanswered_exam_question(user):
    for index, question in enumerate(EXAM):
        if question["id"] not in user["answered"]:
            return index
    return None


def mark_day_completed(user, day_number):
    if day_number not in user["completed_days"]:
        user["completed_days"].append(day_number)
        user["completed_days"].sort()


def score_percent(score):
    if MAX_SCORE <= 0:
        return 0
    value = round(score / MAX_SCORE * 100)
    return max(0, min(100, value))


def rank_for_percent(percent):
    if percent <= 40:
        return "Стажёр, который уже слил пароль"
    if percent <= 70:
        return "Бдительный пользователь"
    if percent <= 90:
        return "Кибер-Джедай"
    return "Хранитель паролей, гроза фишеров"


def get_question_by_id(question_id):
    for day_number, day in DAYS.items():
        for question in day["questions"]:
            if question["id"] == question_id:
                return question, f"День {day_number}"

    for question in EXAM:
        if question["id"] == question_id:
            return question, "Финальный экзамен"

    return None, None


def best_options_text(question):
    best_score = question_max(question)
    best = [
        option["text"]
        for option in question["options"]
        if option["points"] == best_score
    ]
    return " / ".join(best)


def build_review(user):
    mistakes = []
    topics = {}

    for question_id, option_index in user["answered"].items():
        question, section = get_question_by_id(question_id)

        if question is None:
            continue

        try:
            option = question["options"][int(option_index)]
        except (IndexError, TypeError, ValueError):
            continue

        if option["points"] < question_max(question):
            topic = question["topic"]
            topics[topic] = topics.get(topic, 0) + 1

            mistakes.append(
                {
                    "section": section,
                    "topic": topic,
                    "chosen": option["text"],
                    "best": best_options_text(question),
                }
            )

    return mistakes, topics


def send_long_message(chat_id, text, limit=3800):
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at <= 0:
            split_at = limit

        bot.send_message(chat_id, text[:split_at])
        text = text[split_at:].lstrip()

    if text:
        bot.send_message(chat_id, text)


# ============================================================
# /start
# ============================================================

@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    user = get_user(uid)

    if user["name"]:
        bot.send_message(
            message.chat.id,
            f"👋 С возвращением, {user['name']}!\n\n"
            "Стажировка продолжается.\n"
            "Используй /help, чтобы увидеть команды."
        )
        return

    user["awaiting_name"] = True
    save_users()

    bot.send_message(
        message.chat.id,
        "🕵️ Добро пожаловать в ООО «Рога и Копыта Диджитал»!\n\n"
        "Ты — новый сотрудник. В первый день тебе выдали ноутбук, "
        "доступ к корпоративной почте и тревожную записку от уволенного сисадмина:\n\n"
        "«Они уже внутри. Не открывай вложения. "
        "И не говори с “Анной из бухгалтерии”».\n\n"
        "Для начала напиши своё имя, стажёр."
    )


# ============================================================
# /help
# ============================================================

@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "📖 Правила игры\n\n"
        "Ты проходишь 5 дней стажировки по информационной безопасности.\n"
        "В каждом дне нужно выбирать действия в рабочих ситуациях.\n\n"
        "Баллы:\n"
        "• правильный выбор обычно +10;\n"
        "• частично безопасный +3;\n"
        "• опасный выбор даёт штраф.\n\n"
        "Команды:\n"
        "/start — начать или вернуться\n"
        "/day1 … /day5 — дни стажировки\n"
        "/score — текущий результат\n"
        "/final — финальный экзамен и итог\n"
        "/help — эта справка\n"
        "/reset — сбросить свой прогресс для повторного теста\n\n"
        "Дни открываются последовательно."
    )


# ============================================================
# ДНИ 1–5
# ============================================================

def start_or_resume_day(message, day_number):
    if not require_registration(message):
        return

    uid = message.from_user.id
    user = get_user(uid)

    if not all_previous_days_completed(user, day_number):
        missing = next(
            day
            for day in range(1, day_number)
            if day not in user["completed_days"]
        )
        bot.send_message(
            message.chat.id,
            f"🔒 Сначала заверши день {missing}: /day{missing}"
        )
        return

    next_index = next_unanswered_day_question(user, day_number)

    if next_index is None:
        mark_day_completed(user, day_number)
        save_users()

        if day_number < 5:
            bot.send_message(
                message.chat.id,
                f"✅ День {day_number} уже завершён.\n"
                f"Следующий этап: /day{day_number + 1}"
            )
        else:
            bot.send_message(
                message.chat.id,
                "✅ День 5 уже завершён.\n"
                "Можно переходить к финальному экзамену: /final"
            )
        return

    day = DAYS[day_number]

    bot.send_message(
        message.chat.id,
        f"📅 День {day_number}. «{day['title']}»"
    )

    send_day_question(message.chat.id, day_number, next_index)


def send_day_question(chat_id, day_number, question_index):
    question = DAYS[day_number]["questions"][question_index]

    markup = make_keyboard(
        f"day:{day_number}:{question_index}",
        question
    )

    bot.send_message(
        chat_id,
        question["text"],
        reply_markup=markup
    )


@bot.message_handler(commands=["day1"])
def day1(message):
    start_or_resume_day(message, 1)


@bot.message_handler(commands=["day2"])
def day2(message):
    start_or_resume_day(message, 2)


@bot.message_handler(commands=["day3"])
def day3(message):
    start_or_resume_day(message, 3)


@bot.message_handler(commands=["day4"])
def day4(message):
    start_or_resume_day(message, 4)


@bot.message_handler(commands=["day5"])
def day5(message):
    start_or_resume_day(message, 5)


@bot.callback_query_handler(func=lambda call: call.data.startswith("day:"))
def day_answer(call):
    uid = call.from_user.id
    user = get_user(uid)

    if not user["name"]:
        bot.answer_callback_query(call.id, "Сначала отправь /start.")
        return

    try:
        _, day_text, question_text, option_text = call.data.split(":")
        day_number = int(day_text)
        question_index = int(question_text)
        option_index = int(option_text)

        question = DAYS[day_number]["questions"][question_index]
        option = question["options"][option_index]
    except (ValueError, KeyError, IndexError):
        bot.answer_callback_query(call.id, "Не удалось обработать ответ.")
        return

    question_id = question["id"]

    if not all_previous_days_completed(user, day_number):
        bot.answer_callback_query(call.id, "Этот день пока закрыт.")
        return

    expected_index = next_unanswered_day_question(user, day_number)
    if expected_index is None:
        bot.answer_callback_query(call.id, "Этот день уже завершён.")
        remove_keyboard(call)
        return

    if question_index != expected_index:
        bot.answer_callback_query(call.id, "Сначала ответь на предыдущий вопрос.")
        return

    with data_lock:
        if question_id in user["answered"]:
            bot.answer_callback_query(
                call.id,
                "На этот вопрос ты уже отвечал."
            )
            remove_keyboard(call)
            return

        user["answered"][question_id] = option_index
        user["score"] += option["points"]
        save_users()

    bot.answer_callback_query(call.id)
    remove_keyboard(call)

    sign = "+" if option["points"] > 0 else ""
    bot.send_message(
        call.message.chat.id,
        f"{option['feedback']}\n\n"
        f"Баллы за ответ: {sign}{option['points']}\n"
        f"Текущий счёт: {user['score']}"
    )

    next_index = next_unanswered_day_question(user, day_number)

    if next_index is not None:
        send_day_question(
            call.message.chat.id,
            day_number,
            next_index
        )
        return

    with data_lock:
        mark_day_completed(user, day_number)
        save_users()

    if day_number < 5:
        bot.send_message(
            call.message.chat.id,
            f"🎉 День {day_number} завершён!\n\n"
            f"Следующий день: /day{day_number + 1}"
        )
    else:
        bot.send_message(
            call.message.chat.id,
            "🎉 Пять дней стажировки пройдены!\n\n"
            "Теперь тебя ждёт финальный экзамен из 5 вопросов.\n"
            "Подсказок во время экзамена не будет.\n\n"
            "Начать: /final"
        )


# ============================================================
# /score
# ============================================================

@bot.message_handler(commands=["score"])
def score(message):
    if not require_registration(message):
        return

    user = get_user(message.from_user.id)
    percent = score_percent(user["score"])
    completed = len(user["completed_days"])

    bot.send_message(
        message.chat.id,
        f"💰 Текущий счёт: {user['score']} из {MAX_SCORE}\n"
        f"📊 Сейчас это {percent}% от максимума.\n"
        f"📅 Завершено дней: {completed}/5"
    )


# ============================================================
# ФИНАЛЬНЫЙ ЭКЗАМЕН /final
# ============================================================

@bot.message_handler(commands=["final"])
def final(message):
    if not require_registration(message):
        return

    uid = message.from_user.id
    user = get_user(uid)

    if not all(day in user["completed_days"] for day in range(1, 6)):
        missing = next(
            day
            for day in range(1, 6)
            if day not in user["completed_days"]
        )
        bot.send_message(
            message.chat.id,
            f"🔒 До финального экзамена нужно пройти все 5 дней.\n"
            f"Продолжи с /day{missing}"
        )
        return

    next_index = next_unanswered_exam_question(user)

    if next_index is None:
        show_final_result(message.chat.id, user)
        return

    bot.send_message(
        message.chat.id,
        "🧪 Финальный экзамен.\n\n"
        "5 вопросов. Во время экзамена пояснений и подсказок не будет.\n"
        "Результаты и разбор ошибок появятся в конце."
    )

    send_exam_question(message.chat.id, next_index)


def send_exam_question(chat_id, question_index):
    question = EXAM[question_index]

    markup = make_keyboard(
        f"exam:{question_index}",
        question
    )

    bot.send_message(
        chat_id,
        question["text"],
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("exam:"))
def exam_answer(call):
    uid = call.from_user.id
    user = get_user(uid)

    if not user["name"]:
        bot.answer_callback_query(call.id, "Сначала отправь /start.")
        return

    if not all(day in user["completed_days"] for day in range(1, 6)):
        bot.answer_callback_query(call.id, "Сначала заверши все 5 дней.")
        return

    try:
        _, question_text, option_text = call.data.split(":")
        question_index = int(question_text)
        option_index = int(option_text)

        question = EXAM[question_index]
        option = question["options"][option_index]
    except (ValueError, IndexError):
        bot.answer_callback_query(call.id, "Не удалось обработать ответ.")
        return

    question_id = question["id"]

    expected_index = next_unanswered_exam_question(user)
    if expected_index is None:
        bot.answer_callback_query(call.id, "Экзамен уже завершён.")
        remove_keyboard(call)
        return

    if question_index != expected_index:
        bot.answer_callback_query(call.id, "Сначала ответь на предыдущий вопрос.")
        return

    with data_lock:
        if question_id in user["answered"]:
            bot.answer_callback_query(
                call.id,
                "На этот вопрос ты уже отвечал."
            )
            remove_keyboard(call)
            return

        user["answered"][question_id] = option_index
        user["score"] += option["points"]
        save_users()

    bot.answer_callback_query(call.id, "Ответ принят")
    remove_keyboard(call)

    next_index = next_unanswered_exam_question(user)

    if next_index is not None:
        send_exam_question(
            call.message.chat.id,
            next_index
        )
        return

    show_final_result(call.message.chat.id, user)


def show_final_result(chat_id, user):
    percent = score_percent(user["score"])
    rank = rank_for_percent(percent)
    mistakes, topics = build_review(user)

    bot.send_message(
        chat_id,
        f"🏆 Стажировка завершена!\n\n"
        f"Сотрудник: {user['name']}\n"
        f"Итоговый счёт: {user['score']} из {MAX_SCORE}\n"
        f"Результат: {percent}%\n"
        f"Звание: «{rank}»"
    )

    if not mistakes:
        bot.send_message(
            chat_id,
            "🛡 Разбор полётов\n\n"
            "Ты выбрал лучшие варианты во всех ситуациях. "
            "Критичных тем для повторения не обнаружено."
        )
        return

    sorted_topics = sorted(
        topics.items(),
        key=lambda item: item[1],
        reverse=True
    )

    topic_lines = []
    for topic, count in sorted_topics:
        advice = TOPIC_ADVICE.get(topic, "повтори основные правила по этой теме.")
        topic_lines.append(
            f"• {topic}: {count} ошиб. — {advice}"
        )

    bot.send_message(
        chat_id,
        "🛡 Что стоит подтянуть\n\n" + "\n".join(topic_lines)
    )

    review_lines = ["🔎 Разбор выбранных неидеальных ответов\n"]

    for item in mistakes:
        review_lines.append(
            f"• {item['section']} — {item['topic']}\n"
            f"  Ты выбрал: «{item['chosen']}»\n"
            f"  Лучший вариант: «{item['best']}»\n"
        )

    send_long_message(
        chat_id,
        "\n".join(review_lines)
    )


# ============================================================
# /reset — УДОБНО ДЛЯ ТЕСТИРОВАНИЯ
# ============================================================

@bot.message_handler(commands=["reset"])
def reset(message):
    uid = message.from_user.id

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(
            "Да, сбросить",
            callback_data="reset:yes"
        ),
        types.InlineKeyboardButton(
            "Нет",
            callback_data="reset:no"
        )
    )

    bot.send_message(
        message.chat.id,
        "Сбросить имя, очки и весь прогресс?",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("reset:"))
def reset_answer(call):
    uid = call.from_user.id

    if call.data == "reset:no":
        bot.answer_callback_query(call.id, "Сброс отменён")
        remove_keyboard(call)
        return

    with data_lock:
        users[str(uid)] = default_user()
        save_users()

    bot.answer_callback_query(call.id, "Прогресс сброшен")
    remove_keyboard(call)

    bot.send_message(
        call.message.chat.id,
        "♻️ Прогресс удалён.\n"
        "Для новой игры отправь /start."
    )


# ============================================================
# ВВОД ИМЕНИ И ОБЫЧНЫЙ ТЕКСТ
# ============================================================

@bot.message_handler(
    content_types=["text"],
    func=lambda message: bool(message.text) and not message.text.startswith("/")
)
def text_handler(message):
    uid = message.from_user.id
    user = get_user(uid)
    text = message.text.strip()

    if user["awaiting_name"]:
        if not text:
            bot.send_message(
                message.chat.id,
                "Имя не должно быть пустым. Попробуй ещё раз."
            )
            return

        if len(text) > 40:
            bot.send_message(
                message.chat.id,
                "Слишком длинное имя. Введи имя до 40 символов."
            )
            return

        user["name"] = text
        user["awaiting_name"] = False
        save_users()

        bot.send_message(
            message.chat.id,
            f"Отлично, {text}. Добро пожаловать в команду!\n\n"
            "Твоя задача — пережить 5 дней стажировки "
            "и не отдать компанию фишерам.\n\n"
            "Начинай: /day1\n"
            "Правила: /help"
        )
        return

    if user["name"]:
        bot.send_message(
            message.chat.id,
            "Я работаю через команды и кнопки.\n"
            "Посмотреть доступные команды: /help"
        )
    else:
        bot.send_message(
            message.chat.id,
            "Чтобы начать, отправь /start."
        )


# ============================================================
# НЕИЗВЕСТНЫЕ КОМАНДЫ
# ============================================================

@bot.message_handler(
    content_types=["text"],
    func=lambda message: bool(message.text) and message.text.startswith("/")
)
def unknown_command(message):
    bot.send_message(
        message.chat.id,
        "Неизвестная команда.\n"
        "Список доступных команд: /help"
    )


# ============================================================
# ЗАПУСК
# ============================================================

def setup_commands():
    bot.set_my_commands([
        types.BotCommand("start", "Начать стажировку"),
        types.BotCommand("day1", "День 1 — пароли"),
        types.BotCommand("day2", "День 2 — фишинг"),
        types.BotCommand("day3", "День 3 — социнженерия"),
        types.BotCommand("day4", "День 4 — USB и передача файлов"),
        types.BotCommand("day5", "День 5 — чистый стол"),
        types.BotCommand("score", "Текущий счёт"),
        types.BotCommand("final", "Финальный экзамен"),
        types.BotCommand("help", "Правила и команды"),
        types.BotCommand("reset", "Сбросить прогресс"),
    ])


def main():
    setup_commands()
    print(f"Бот запущен. Максимальный балл: {MAX_SCORE}")
    bot.infinity_polling(
        skip_pending=True,
        timeout=30
    )


if __name__ == "__main__":
    main()
