import os
import csv
from dotenv import load_dotenv
from datetime import datetime, timedelta

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from database import (
    init_db,
    add_appointment,
    get_appointments,
    is_slot_busy,
    get_busy_slots,
    delete_appointment,
    find_appointments_by_phone,
    get_finance_stats,
    get_all_clients,
    clear_appointments,
    get_client_history
)

from ai import ask_ai

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = 6064588259

init_db()
user_states = {}

client_keyboard = ReplyKeyboardMarkup(
    [
        ["📝 Записаться"],
        ["📆 Расписание"],
        ["🕒 Свободное время"]
        ["💰 Цены"],
        ["📍 Контакты"]
    ],
    resize_keyboard=True
)

admin_keyboard = ReplyKeyboardMarkup(
    [
        ["📅 Сегодняшние записи"],
        ["📝 Записаться"],
        ["📆 Расписание"],
        ["📋 Заявки"],
        ["👥 Мастера"],
        ["🕒 Свободное время"]
        ["💰 Цены"],
        ["📍 Контакты"]
    ],
    resize_keyboard=True
)

service_keyboard = ReplyKeyboardMarkup(
    [["✂️ Стрижка"], ["🧔 Борода"], ["💈 Комплекс"]],
    resize_keyboard=True
)

barber_keyboard = ReplyKeyboardMarkup(
    [["💈 Али"], ["💈 Рашад"], ["💈 Эльвин"]],
    resize_keyboard=True
)

date_keyboard = ReplyKeyboardMarkup(
    [["📅 Сегодня"], ["📅 Завтра"], ["📅 Другая дата"]],
    resize_keyboard=True
)

time_keyboard = ReplyKeyboardMarkup(
    [
        ["🕙 10:00", "🕚 11:00"],
        ["🕛 12:00", "🕐 13:00"],
        ["🕑 14:00", "🕒 15:00"]
    ],
    resize_keyboard=True
)

BARBERS = ["💈 Али", "💈 Рашад", "💈 Эльвин"]
ALL_SLOTS = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00"]
BUSINESS_NAME = "Barber House"
BUSINESS_ADDRESS = "Баку, адрес будет тут"
BUSINESS_PHONE = "+994 XX XXX XX XX"
PRICES = {
    "✂️ Стрижка": "15 AZN",
    "🧔 Борода": "10 AZN",
    "💈 Комплекс": "20 AZN"
}


def is_admin(update):
    return update.effective_user.id == OWNER_ID


def get_keyboard(update):
    if is_admin(update):
        return admin_keyboard
    return client_keyboard


def today_date():
    return datetime.now().strftime("%d.%m.%Y")


def tomorrow_date():
    return (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")


def normalize_date(text):
    if text == "📅 Сегодня":
        return today_date()
    if text == "📅 Завтра":
        return tomorrow_date()
    return text.strip()


def clean_time(text):
    return (
        text.replace("🕙 ", "")
        .replace("🕚 ", "")
        .replace("🕛 ", "")
        .replace("🕐 ", "")
        .replace("🕑 ", "")
        .replace("🕒 ", "")
        .strip()
    )


def get_free_slots_text(appointment_date):
    busy_slots = get_busy_slots(appointment_date)
    text = f"🕒 Свободное время на {appointment_date}:\n\n"

    for slot in ALL_SLOTS:
        if slot in busy_slots:
            text += f"❌ {slot} занято\n"
        else:
            text += f"✅ {slot} свободно\n"

    return text


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.", reply_markup=get_keyboard(update))
        return

    appointments = get_appointments()
    text = "📅 Записи на сегодня:\n\n"
    found = False

    for appointment in appointments:
        if appointment["date"] == today_date():
            found = True
            text += (
                f"ID: {appointment['id']}\n"
                f"👤 {appointment['name']}\n"
                f"✂️ {appointment['service']}\n"
                f"💈 Мастер: {appointment['barber']}\n"
                f"🕒 {appointment['time']}\n"
                f"📞 {appointment['phone']}\n\n"
            )

    if not found:
        text = "На сегодня записей нет."

    await update.message.reply_text(text, reply_markup=get_keyboard(update))


async def tomorrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.", reply_markup=get_keyboard(update))
        return

    appointments = get_appointments()
    text = "📅 Записи на завтра:\n\n"
    found = False

    for appointment in appointments:
        if appointment["date"] == tomorrow_date():
            found = True
            text += (
                f"ID: {appointment['id']}\n"
                f"👤 {appointment['name']}\n"
                f"✂️ {appointment['service']}\n"
                f"💈 Мастер: {appointment['barber']}\n"
                f"🕒 {appointment['time']}\n"
                f"📞 {appointment['phone']}\n\n"
            )

    if not found:
        text = "На завтра записей нет."

    await update.message.reply_text(text, reply_markup=get_keyboard(update))


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.", reply_markup=get_keyboard(update))
        return

    appointments = get_appointments()

    if not appointments:
        await update.message.reply_text("Заявок пока нет.", reply_markup=get_keyboard(update))
        return

    filename = "appointments_export.csv"

    with open(filename, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Имя", "Услуга", "Мастер", "Дата", "Время", "Телефон"])

        for appointment in appointments:
            writer.writerow([
                appointment["id"],
                appointment["name"],
                appointment["service"],
                appointment["barber"],
                appointment["date"],
                appointment["time"],
                appointment["phone"]
            ])

    with open(filename, "rb") as file:
        await update.message.reply_document(document=file, filename=filename, caption="📁 Экспорт заявок")


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.", reply_markup=get_keyboard(update))
        return

    clear_appointments()
    await update.message.reply_text("🧹 Все заявки удалены.", reply_markup=get_keyboard(update))


async def clients_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.", reply_markup=get_keyboard(update))
        return

    clients = get_all_clients()

    if not clients:
        await update.message.reply_text("Клиентов пока нет.", reply_markup=get_keyboard(update))
        return

    text = "👥 База клиентов\n\n"

    for phone, name in clients.items():
        text += f"👤 {name}\n📞 {phone}\n\n"

    await update.message.reply_text(text[:4000], reply_markup=get_keyboard(update))


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.", reply_markup=get_keyboard(update))
        return

    appointments = get_appointments()

    total = len(appointments)
    haircut = 0
    beard = 0
    combo = 0
    today_count = 0
    tomorrow_count = 0

    for appointment in appointments:
        service = appointment["service"]
        date = appointment["date"]

        if "Стрижка" in service:
            haircut += 1
        if "Борода" in service:
            beard += 1
        if "Комплекс" in service:
            combo += 1
        if date == today_date():
            today_count += 1
        if date == tomorrow_date():
            tomorrow_count += 1

    text = (
        "📊 Статистика записей\n\n"
        f"Всего записей: {total}\n\n"
        f"Сегодня: {today_count}\n"
        f"Завтра: {tomorrow_count}\n\n"
        f"✂️ Стрижка: {haircut}\n"
        f"🧔 Борода: {beard}\n"
        f"💈 Комплекс: {combo}"
    )

    await update.message.reply_text(text, reply_markup=get_keyboard(update))


async def finance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.", reply_markup=get_keyboard(update))
        return

    stats = get_finance_stats()

    text = (
        "💰 Финансы\n\n"
        f"✂️ Стрижка: {stats['haircut']} AZN\n"
        f"🧔 Борода: {stats['beard']} AZN\n"
        f"💈 Комплекс: {stats['combo']} AZN\n\n"
        f"💵 Итого: {stats['total']} AZN"
    )

    await update.message.reply_text(text, reply_markup=get_keyboard(update))


async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.", reply_markup=get_keyboard(update))
        return

    filename = "appointments.db"

    if not os.path.exists(filename):
        await update.message.reply_text("❌ База данных не найдена.", reply_markup=get_keyboard(update))
        return

    with open(filename, "rb") as file:
        await update.message.reply_document(document=file, filename=filename, caption="🗄 Резервная копия базы данных")


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.", reply_markup=get_keyboard(update))
        return

    if len(context.args) != 1:
        await update.message.reply_text("Использование: /delete ID", reply_markup=get_keyboard(update))
        return

    try:
        appointment_id = int(context.args[0])
        delete_appointment(appointment_id)
        await update.message.reply_text(f"✅ Запись #{appointment_id} удалена.", reply_markup=get_keyboard(update))
    except Exception:
        await update.message.reply_text("❌ Неверный ID.", reply_markup=get_keyboard(update))


async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.", reply_markup=get_keyboard(update))
        return

    if len(context.args) != 1:
        await update.message.reply_text("Использование: /find НОМЕР", reply_markup=get_keyboard(update))
        return

    phone = context.args[0]
    results = find_appointments_by_phone(phone)

    if not results:
        await update.message.reply_text("❌ Записи не найдены.", reply_markup=get_keyboard(update))
        return

    text = "📞 Найденные записи:\n\n"

    for appointment in results:
        text += (
            f"ID: {appointment['id']}\n"
            f"Имя: {appointment['name']}\n"
            f"Услуга: {appointment['service']}\n"
            f"💈 Мастер: {appointment.get('barber', '')}\n"
            f"Дата: {appointment['date']}\n"
            f"Время: {appointment['time']}\n"
            f"Телефон: {appointment['phone']}\n\n"
        )

    await update.message.reply_text(text[:4000], reply_markup=get_keyboard(update))

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "Использование: /history НОМЕР"
        )
        return

    phone = context.args[0]

    history = get_client_history(phone)

    if not history:
        await update.message.reply_text(
            "История не найдена."
        )
        return

    text = f"📖 История клиента\n\n📞 {phone}\n\n"

    text += f"Посещений: {len(history)}\n\n"

    for record in history:
        text += (
            f"📅 {record[2]}\n"
            f"🕒 {record[3]}\n"
            f"💈 {record[1]}\n"
            f"✂️ {record[0]}\n\n"
        )

    await update.message.reply_text(text[:4000])


async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    action = parts[0]

    if action == "approve":
        appointment_id = int(parts[1])
        telegram_id = int(parts[2])

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отменить запись", callback_data=f"client_cancel:{appointment_id}")]
        ])

        await context.bot.send_message(
            chat_id=telegram_id,
            text="✅ Ваша запись подтверждена.",
            reply_markup=keyboard
        )

        await query.edit_message_text(query.message.text + "\n\n✅ Подтверждено")
        return

    if action == "reject":
        appointment_id = int(parts[1])
        telegram_id = int(parts[2])

        delete_appointment(appointment_id)

        await context.bot.send_message(chat_id=telegram_id, text="❌ К сожалению, запись отклонена.")
        await query.edit_message_text(query.message.text + "\n\n❌ Отклонено")
        return

    if action == "client_cancel" or action == "cancel":
        appointment_id = int(parts[1])

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Да, отменить", callback_data=f"confirm_client_cancel:{appointment_id}"),
                InlineKeyboardButton("⬅️ Нет", callback_data="dont_cancel")
            ]
        ])

        await query.edit_message_text(
            query.message.text + "\n\nВы уверены, что хотите отменить запись?",
            reply_markup=keyboard
        )
        return

    if action == "confirm_client_cancel":
        appointment_id = int(parts[1])
        delete_appointment(appointment_id)

        await query.edit_message_text("✅ Запись отменена.")
        await context.bot.send_message(chat_id=OWNER_ID, text=f"⚠️ Клиент отменил запись #{appointment_id}")
        return

    if action == "dont_cancel":
        await query.edit_message_text("Окей, запись не отменена ✅")
        return


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = str(update.effective_user.id)
    message_lower = user_message.lower()

    cancel_words = ["отменить запись", "отмена записи", "хочу отменить", "удалить запись"]

    if any(word in message_lower for word in cancel_words):
        user_states[user_id] = {"step": "cancel_phone"}

        await update.message.reply_text(
            "Введите номер телефона, который указывали при записи:",
            reply_markup=get_keyboard(update)
        )
        return

    if message_lower in ["свободное время", "свободные слоты", "🕒 свободное время"]:
        await update.message.reply_text(
            get_free_slots_text(today_date()),
            reply_markup=get_keyboard(update)
        )
        return

    if message_lower in ["📅 сегодняшние записи", "сегодняшние записи"]:
        await today_command(update, context)
        return
    
        if message_lower in ["💰 цены", "цены", "прайс"]:
         text = "💰 Цены\n\n"

        for service, price in PRICES.items():
            text += f"{service} — {price}\n"

        await update.message.reply_text(
            text,
            reply_markup=get_keyboard(update)
        )
        return

    if message_lower in ["📍 контакты", "контакты", "адрес"]:
        text = (
            f"📍 {BUSINESS_NAME}\n\n"
            f"Адрес: {BUSINESS_ADDRESS}\n"
            f"Телефон: {BUSINESS_PHONE}\n\n"
            "🕒 Время работы: 10:00 - 15:00"
        )

        await update.message.reply_text(
            text,
            reply_markup=get_keyboard(update)
        )
        return

    if message_lower in ["📆 расписание", "расписание"]:
        appointments = get_appointments()
        text = "📆 Расписание на 7 дней\n\n"

        for i in range(7):
            date = (datetime.now() + timedelta(days=i)).strftime("%d.%m.%Y")
            text += f"📅 {date}\n\n"

            for barber in BARBERS:
                text += f"{barber}\n"

                for slot in ALL_SLOTS:
                    busy = False

                    for appointment in appointments:
                        if (
                            appointment["date"] == date
                            and appointment["time"] == slot
                            and appointment["barber"] == barber
                        ):
                            busy = True
                            break

                    if busy:
                        text += f"❌ {slot} занято\n"
                    else:
                        text += f"✅ {slot} свободно\n"

                text += "\n"

            text += "────────────\n\n"

        await update.message.reply_text(text[:4000], reply_markup=get_keyboard(update))
        return
    
    if message_lower in ["💰 цены", "цены", "прайс"]:
     text = "💰 Цены\n\n"

    for service, price in PRICES.items():
        text += f"{service} — {price}\n"

    await update.message.reply_text(
        text,
        reply_markup=get_keyboard(update)
    )
    return

    if message_lower in ["📍 контакты", "контакты", "адрес"]:
     text = (
        f"📍 {BUSINESS_NAME}\n\n"
        f"Адрес: {BUSINESS_ADDRESS}\n"
        f"Телефон: {BUSINESS_PHONE}\n\n"
        "🕒 Время работы: 10:00 - 15:00"
    )

    await update.message.reply_text(
        text,
        reply_markup=get_keyboard(update)
    )
    return

    if user_id in user_states:
        state = user_states[user_id]

        if state["step"] == "cancel_phone":
            phone = user_message
            results = find_appointments_by_phone(phone)

            del user_states[user_id]

            if not results:
                await update.message.reply_text(
                    "❌ Записи по этому номеру не найдены.",
                    reply_markup=get_keyboard(update)
                )
                return

            text = "📞 Найденные записи:\n\n"
            keyboard_buttons = []

            for appointment in results:
                text += (
                    f"ID: {appointment['id']}\n"
                    f"Имя: {appointment['name']}\n"
                    f"Услуга: {appointment['service']}\n"
                    f"Дата: {appointment['date']}\n"
                    f"Время: {appointment['time']}\n"
                    f"Телефон: {appointment['phone']}\n\n"
                )

                keyboard_buttons.append([
                    InlineKeyboardButton(
                        f"❌ Отменить запись #{appointment['id']}",
                        callback_data=f"cancel:{appointment['id']}"
                    )
                ])

            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            await update.message.reply_text(text[:4000], reply_markup=keyboard)
            return

        if state["step"] == "name":
            state["name"] = user_message
            state["step"] = "service"

            await update.message.reply_text("Выберите услугу:", reply_markup=service_keyboard)
            return

        if state["step"] == "service":
            state["service"] = user_message
            state["step"] = "barber"

            await update.message.reply_text("Выберите мастера:", reply_markup=barber_keyboard)
            return

        if state["step"] == "barber":
            state["barber"] = user_message
            state["step"] = "date"

            await update.message.reply_text("Выберите дату:", reply_markup=date_keyboard)
            return

        if state["step"] == "date":
            if user_message == "📅 Другая дата":
                state["step"] = "custom_date"
                await update.message.reply_text("Напишите дату, например: 20.06.2026")
                return

            state["date"] = normalize_date(user_message)
            state["step"] = "time"

            await update.message.reply_text("Выберите время:", reply_markup=time_keyboard)
            return

        if state["step"] == "custom_date":
            state["date"] = normalize_date(user_message)
            state["step"] = "time"

            await update.message.reply_text("Выберите время:", reply_markup=time_keyboard)
            return

        if state["step"] == "time":
            selected_time = clean_time(user_message)

            if is_slot_busy(state["date"], selected_time, state["barber"]):
                await update.message.reply_text(
                    "❌ Это время уже занято. Выберите другое.",
                    reply_markup=time_keyboard
                )
                return

            state["time"] = selected_time
            state["step"] = "phone"

            await update.message.reply_text("Оставьте номер телефона:")
            return

        if state["step"] == "phone":
            state["phone"] = user_message

            appointment_id = add_appointment(
                state["name"],
                state["service"],
                state["barber"],
                state["date"],
                state["time"],
                state["phone"],
                state["telegram_id"]
            )

            try:
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "✅ Подтвердить",
                            callback_data=f"approve:{appointment_id}:{state['telegram_id']}"
                        ),
                        InlineKeyboardButton(
                            "❌ Отклонить",
                            callback_data=f"reject:{appointment_id}:{state['telegram_id']}"
                        )
                    ]
                ])

                await context.bot.send_message(
                    chat_id=OWNER_ID,
                    text=(
                        "🚨 Новая заявка\n\n"
                        f"Имя: {state['name']}\n"
                        f"Услуга: {state['service']}\n"
                        f"💈 Мастер: {state['barber']}\n"
                        f"Дата: {state['date']}\n"
                        f"Время: {state['time']}\n"
                        f"Телефон: {state['phone']}"
                    ),
                    reply_markup=keyboard
                )

            except Exception as e:
                print("Ошибка уведомления владельцу:", e)

            del user_states[user_id]

            await update.message.reply_text(
                "✅ Заявка сохранена. Ожидайте подтверждения.",
                reply_markup=get_keyboard(update)
            )
            return

    if message_lower in ["старт", "start", "привет", "меню"]:
        await update.message.reply_text(
            "Привет! Я бот для записи клиентов.\n\n"
            "Нажмите «📝 Записаться», чтобы оставить заявку.",
            reply_markup=get_keyboard(update)
        )
        return

    if message_lower in ["записаться", "📝 записаться"]:
        user_states[user_id] = {
            "step": "name",
            "telegram_id": update.effective_user.id
        }

        await update.message.reply_text("Как вас зовут?")
        return

    if message_lower in ["👥 мастера", "мастера"]:
        if not is_admin(update):
            await update.message.reply_text(
                "⛔ У вас нет доступа к этому разделу.",
                reply_markup=get_keyboard(update)
            )
            return

        appointments = get_appointments()

        if not appointments:
            await update.message.reply_text("Записей пока нет.", reply_markup=get_keyboard(update))
            return

        barbers = {}

        for appointment in appointments:
            barber = appointment["barber"]

            if barber not in barbers:
                barbers[barber] = []

            barbers[barber].append(appointment)

        text = "👥 Расписание мастеров\n\n"

        for barber, records in barbers.items():
            text += f"{barber}\n\n"

            for record in records:
                text += (
                    f"{record['date']} | "
                    f"{record['time']} | "
                    f"{record['name']}\n"
                )

            text += "\n"

        await update.message.reply_text(text[:4000], reply_markup=get_keyboard(update))
        return

    if message_lower in ["заявки", "📋 заявки"]:
        if not is_admin(update):
            await update.message.reply_text(
                "⛔ У вас нет доступа к заявкам.",
                reply_markup=get_keyboard(update)
            )
            return

        appointments = get_appointments()

        if not appointments:
            await update.message.reply_text("Заявок пока нет", reply_markup=get_keyboard(update))
            return

        text = "📋 Заявки:\n\n"

        for appointment in appointments:
            text += (
                f"{appointment['id']}.\n"
                f"Имя: {appointment['name']}\n"
                f"Услуга: {appointment['service']}\n"
                f"💈 Мастер: {appointment['barber']}\n"
                f"Дата: {appointment['date']}\n"
                f"Время: {appointment['time']}\n"
                f"Телефон: {appointment['phone']}\n\n"
            )

        await update.message.reply_text(text[:4000], reply_markup=get_keyboard(update))
        return

    booking_words = [
        "записаться",
        "запись",
        "запишите",
        "хочу прийти",
        "можно записаться",
        "хочу на стрижку",
        "хочу подстричься"
    ]

    if any(word in message_lower for word in booking_words):
        await update.message.reply_text(
            "Конечно ✅\nНажмите кнопку «📝 Записаться», и я оформлю заявку.",
            reply_markup=get_keyboard(update)
        )
        return

    free_slots = []

    for slot in ALL_SLOTS:
        if slot not in get_busy_slots(today_date()):
            free_slots.append(slot)

    answer = ask_ai(user_message, ", ".join(free_slots))

    await update.message.reply_text(answer, reply_markup=get_keyboard(update))


async def send_tomorrow_reminders(context: ContextTypes.DEFAULT_TYPE):
    print("Проверка напоминаний...")
    print(get_appointments())

    appointments = get_appointments()
    tomorrow = tomorrow_date()

    for appointment in appointments:
        if appointment["date"] == tomorrow and appointment["telegram_id"]:
            try:
                await context.bot.send_message(
                    chat_id=int(appointment["telegram_id"]),
                    text=(
                        "🔔 Напоминание о записи\n\n"
                        "Вы записаны на завтра.\n\n"
                        f"✂️ Услуга: {appointment['service']}\n"
                        f"💈 Мастер: {appointment['barber']}\n"
                        f"📅 Дата: {appointment['date']}\n"
                        f"🕒 Время: {appointment['time']}\n\n"
                        "Ждём вас!"
                    )
                )
            except Exception as e:
                print("Ошибка напоминания:", e)


app = ApplicationBuilder().token(TOKEN).build()

app.job_queue.run_repeating(
    send_tomorrow_reminders,
    interval=86400,
    first=10
)

app.add_handler(CommandHandler("today", today_command))
app.add_handler(CommandHandler("tomorrow", tomorrow_command))
app.add_handler(CommandHandler("delete", delete_command))
app.add_handler(CommandHandler("find", find_command))
app.add_handler(CommandHandler("stats", stats_command))
app.add_handler(CommandHandler("finance", finance_command))
app.add_handler(CommandHandler("history", history_command))
app.add_handler(CommandHandler("clients", clients_command))
app.add_handler(CommandHandler("export", export_command))
app.add_handler(CommandHandler("backup", backup_command))
app.add_handler(CommandHandler("clear", clear_command))
app.add_handler(CallbackQueryHandler(handle_approval))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    )
)

print("Appointment Bot запущен")

app.run_polling()