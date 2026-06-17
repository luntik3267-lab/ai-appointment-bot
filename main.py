import os
import csv
from dotenv import load_dotenv

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

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
    get_all_clients
)

from ai import ask_ai

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = 6064588259

def is_admin(update):
    return update.effective_user.id == OWNER_ID

init_db()

user_states = {}

main_keyboard = ReplyKeyboardMarkup(
    [
        ["📅 Сегодняшние записи"],
        ["📝 Записаться"],
        ["📋 Заявки"],
        ["🕒 Свободное время"]
    ],
    resize_keyboard=True
)

service_keyboard = ReplyKeyboardMarkup(
    [
        ["✂️ Стрижка"],
        ["🧔 Борода"],
        ["💈 Комплекс"]
    ],
    resize_keyboard=True
)

date_keyboard = ReplyKeyboardMarkup(
    [
        ["📅 Сегодня"],
        ["📅 Завтра"],
        ["📅 Другая дата"]
    ],
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
    all_slots = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00"]
    busy_slots = get_busy_slots(appointment_date)

    text = f"🕒 Свободное время на {appointment_date}:\n\n"

    for slot in all_slots:
        if slot in busy_slots:
            text += f"❌ {slot} занято\n"
        else:
            text += f"✅ {slot} свободно\n"

    return text


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):

        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")

        return

    appointments = get_appointments()

    text = "📅 Записи на сегодня:\n\n"

    found = False

    for appointment in appointments:

        if appointment["date"] == "Сегодня":

            found = True

            text += (

                f"ID: {appointment['id']}\n"

                f"👤 {appointment['name']}\n"

                f"✂️ {appointment['service']}\n"

                f"🕒 {appointment['time']}\n"

                f"📞 {appointment['phone']}\n\n"

            )

    if not found:

        text = "На сегодня записей нет."

    await update.message.reply_text(text, reply_markup=main_keyboard)

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        await update.message.reply_text(
            "⛔ У вас нет доступа к этой команде."
        )
        return

    appointments = get_appointments()

    if not appointments:
        await update.message.reply_text(
            "Заявок пока нет.",
            reply_markup=main_keyboard
        )
        return

    filename = "appointments_export.csv"

    with open(filename, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)

        writer.writerow([
            "ID",
            "Имя",
            "Услуга",
            "Дата",
            "Время",
            "Телефон"
        ])

        for appointment in appointments:
            writer.writerow([
                appointment["id"],
                appointment["name"],
                appointment["service"],
                appointment["date"],
                appointment["time"],
                appointment["phone"]
            ])

    await update.message.reply_document(
        document=open(filename, "rb"),
        filename=filename,
        caption="📁 Экспорт заявок"
    )


async def tomorrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):

        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")

        return

    appointments = get_appointments()

    text = "📅 Записи на завтра:\n\n"

    found = False

    for appointment in appointments:

        if appointment["date"] == "Завтра":

            found = True

            text += (

                f"ID: {appointment['id']}\n"

                f"👤 {appointment['name']}\n"

                f"✂️ {appointment['service']}\n"

                f"🕒 {appointment['time']}\n"

                f"📞 {appointment['phone']}\n\n"

            )

    if not found:

        text = "На завтра записей нет."

    await update.message.reply_text(text, reply_markup=main_keyboard)

async def clients_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        await update.message.reply_text(
            "⛔ У вас нет доступа к этой команде."
        )
        return

    clients = get_all_clients()

    if not clients:
        await update.message.reply_text("Клиентов пока нет.")
        return

    text = "👥 База клиентов\n\n"

    for phone, name in clients.items():
        text += (
            f"👤 {name}\n"
            f"📞 {phone}\n\n"
        )

    await update.message.reply_text(text[:4000])


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):

        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")

        return

    appointments = get_appointments()

    total = len(appointments)

    haircut = 0

    beard = 0

    combo = 0

    today = 0

    tomorrow = 0

    for appointment in appointments:

        service = appointment["service"]

        date = appointment["date"]

        if "Стрижка" in service:

            haircut += 1

        if "Борода" in service:

            beard += 1

        if "Комплекс" in service:

            combo += 1

        if date == "Сегодня":

            today += 1

        if date == "Завтра":

            tomorrow += 1

    text = (

        "📊 Статистика записей\n\n"

        f"Всего записей: {total}\n\n"

        f"Сегодня: {today}\n"

        f"Завтра: {tomorrow}\n\n"

        f"✂️ Стрижка: {haircut}\n"

        f"🧔 Борода: {beard}\n"

        f"💈 Комплекс: {combo}"

    )

    await update.message.reply_text(text, reply_markup=main_keyboard)


async def finance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        await update.message.reply_text(
            "⛔ У вас нет доступа к этой команде."
        )
        return

    stats = get_finance_stats()

    text = (
        "💰 Финансы\n\n"
        f"✂️ Стрижка: {stats['haircut']} AZN\n"
        f"🧔 Борода: {stats['beard']} AZN\n"
        f"💈 Комплекс: {stats['combo']} AZN\n\n"
        f"💵 Итого: {stats['total']} AZN"
    )

    await update.message.reply_text(
        text,
        reply_markup=main_keyboard
    )


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if not is_admin(update):
        await update.message.reply_text(
            "⛔ У вас нет доступа к этой команде."
        )
        return

    if len(context.args) != 1:
        await update.message.reply_text("Использование: /delete ID")
        return

    try:
        appointment_id = int(context.args[0])
        delete_appointment(appointment_id)

        await update.message.reply_text(
            f"✅ Запись #{appointment_id} удалена.",
            reply_markup=main_keyboard
        )

    except Exception:
        await update.message.reply_text(
            "❌ Неверный ID.",
            reply_markup=main_keyboard
        )


async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        await update.message.reply_text(
            "⛔ У вас нет доступа к этой команде."
        )
        return
    if len(context.args) != 1:
        await update.message.reply_text("Использование: /find НОМЕР")
        return

    phone = context.args[0]
    results = find_appointments_by_phone(phone)

    if not results:
        await update.message.reply_text(
            "❌ Записи не найдены.",
            reply_markup=main_keyboard
        )
        return

    text = "📞 Найденные записи:\n\n"

    for appointment in results:
        text += (
            f"ID: {appointment['id']}\n"
            f"Имя: {appointment['name']}\n"
            f"Услуга: {appointment['service']}\n"
            f"Дата: {appointment['date']}\n"
            f"Время: {appointment['time']}\n"
            f"Телефон: {appointment['phone']}\n\n"
        )

    await update.message.reply_text(
        text[:4000],
        reply_markup=main_keyboard
    )


async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, telegram_id = query.data.split(":")
    telegram_id = int(telegram_id)

    if action == "approve":
        await context.bot.send_message(
            chat_id=telegram_id,
            text="✅ Ваша запись подтверждена."
        )

        await query.edit_message_text(
            query.message.text + "\n\n✅ Подтверждено"
        )

    elif action == "reject":
        await context.bot.send_message(
            chat_id=telegram_id,
            text="❌ К сожалению, запись отклонена."
        )

        await query.edit_message_text(
            query.message.text + "\n\n❌ Отклонено"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = str(update.effective_user.id)
    message_lower = user_message.lower()

    cancel_words = [
        "отменить запись",
        "отмена записи",
        "хочу отменить",
        "удалить запись"
    ]

    if any(word in message_lower for word in cancel_words):
        user_states[user_id] = {
            "step": "cancel_phone"
        }

        await update.message.reply_text(
            "Введите номер телефона, который указывали при записи:"
        )
        return

    if message_lower in ["свободное время", "свободные слоты", "🕒 свободное время"]:
        await update.message.reply_text(
            get_free_slots_text("Сегодня"),
            reply_markup=main_keyboard
        )
        return

    if message_lower in ["📅 сегодняшние записи", "сегодняшние записи"]:
        await today_command(update, context)
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
                    reply_markup=main_keyboard
                )
                return

            text = "📞 Найденные записи:\n\n"

            for appointment in results:
                text += (
                    f"ID: {appointment['id']}\n"
                    f"Имя: {appointment['name']}\n"
                    f"Услуга: {appointment['service']}\n"
                    f"Дата: {appointment['date']}\n"
                    f"Время: {appointment['time']}\n"
                    f"Телефон: {appointment['phone']}\n\n"
                )

            text += "Чтобы отменить запись, напишите:\n/delete ID"

            await update.message.reply_text(
                text[:4000],
                reply_markup=main_keyboard
            )
            return

        if state["step"] == "name":
            state["name"] = user_message
            state["step"] = "service"

            await update.message.reply_text(
                "Выберите услугу:",
                reply_markup=service_keyboard
            )
            return

        if state["step"] == "service":
            state["service"] = user_message
            state["step"] = "date"

            await update.message.reply_text(
                "Выберите дату:",
                reply_markup=date_keyboard
            )
            return

        if state["step"] == "date":
            if user_message == "📅 Сегодня":
                state["date"] = "Сегодня"

            elif user_message == "📅 Завтра":
                state["date"] = "Завтра"

            elif user_message == "📅 Другая дата":
                state["step"] = "custom_date"

                await update.message.reply_text(
                    "Напишите дату, например: 20 июня"
                )
                return

            else:
                state["date"] = user_message

            state["step"] = "time"

            await update.message.reply_text(
                "Выберите время:",
                reply_markup=time_keyboard
            )
            return

        if state["step"] == "custom_date":
            state["date"] = user_message
            state["step"] = "time"

            await update.message.reply_text(
                "Выберите время:",
                reply_markup=time_keyboard
            )
            return

        if state["step"] == "time":
            selected_time = clean_time(user_message)

            if is_slot_busy(state["date"], selected_time):
                await update.message.reply_text(
                    "❌ Это время уже занято. Выберите другое.",
                    reply_markup=time_keyboard
                )
                return

            state["time"] = selected_time
            state["step"] = "phone"

            await update.message.reply_text(
                "Оставьте номер телефона:"
            )
            return

        if state["step"] == "phone":
            state["phone"] = user_message

            add_appointment(
                state["name"],
                state["service"],
                state["date"],
                state["time"],
                state["phone"]
            )

            try:
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "✅ Подтвердить",
                            callback_data=f"approve:{state['telegram_id']}"
                        ),
                        InlineKeyboardButton(
                            "❌ Отклонить",
                            callback_data=f"reject:{state['telegram_id']}"
                        )
                    ]
                ])

                await context.bot.send_message(
                    chat_id=OWNER_ID,
                    text=(
                        "🚨 Новая заявка\n\n"
                        f"Имя: {state['name']}\n"
                        f"Услуга: {state['service']}\n"
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
                reply_markup=main_keyboard
            )
            return

    if message_lower in ["старт", "start", "привет", "меню"]:
        await update.message.reply_text(
            "Привет! Я бот для записи клиентов.\n\n"
            "Нажмите «📝 Записаться», чтобы оставить заявку.",
            reply_markup=main_keyboard
        )
        return

    if message_lower in ["записаться", "📝 записаться"]:
        user_states[user_id] = {
            "step": "name",
            "telegram_id": update.effective_user.id
        }

        await update.message.reply_text("Как вас зовут?")
        return

    if message_lower in ["заявки", "📋 заявки"]:
        appointments = get_appointments()

        if not appointments:
            await update.message.reply_text(
                "Заявок пока нет",
                reply_markup=main_keyboard
            )
            return

        text = "📋 Заявки:\n\n"

        for appointment in appointments:
            text += (
                f"{appointment['id']}.\n"
                f"Имя: {appointment['name']}\n"
                f"Услуга: {appointment['service']}\n"
                f"Дата: {appointment['date']}\n"
                f"Время: {appointment['time']}\n"
                f"Телефон: {appointment['phone']}\n\n"
            )

        await update.message.reply_text(
            text[:4000],
            reply_markup=main_keyboard
        )
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
            reply_markup=main_keyboard
        )
        return

    all_slots = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00"]
    busy_slots = get_busy_slots("Сегодня")

    free_slots = []

    for slot in all_slots:
        if slot not in busy_slots:
            free_slots.append(slot)

    answer = ask_ai(
        user_message,
        ", ".join(free_slots)
    )

    await update.message.reply_text(
        answer,
        reply_markup=main_keyboard
    )


app = (
    ApplicationBuilder()
    .token(TOKEN)
    .build()
)

app.add_handler(CommandHandler("today", today_command))
app.add_handler(CommandHandler("tomorrow", tomorrow_command))
app.add_handler(CommandHandler("delete", delete_command))
app.add_handler(CommandHandler("find", find_command))
app.add_handler(CommandHandler("stats", stats_command))
app.add_handler(CommandHandler("finance", finance_command))
app.add_handler(CommandHandler("clients", clients_command))
app.add_handler(CommandHandler("export", export_command))
app.add_handler(CallbackQueryHandler(handle_approval))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    )
)

print("Appointment Bot запущен")

app.run_polling()