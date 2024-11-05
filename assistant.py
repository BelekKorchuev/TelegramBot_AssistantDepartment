import asyncio
import os
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
from constants_and_google import SENDING_RECEIPT, sheet, GET_NAME, GET_AMOUNT, GET_PLACE, GET_DATE, CHOOSING_CATEGORY
from head_assistant import load_assistants, load_categories
import logging
from telegram.error import BadRequest

PHOTO_GROUP_CHAT_ID = -1002185965826

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def choose_category(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = str(query.from_user.id)
    authorized_assistants = load_assistants()

    # Проверка, есть ли ассистент в системе
    if user_id not in authorized_assistants:
        await query.answer("У вас нет доступа к системе. Пожалуйста, обратитесь к руководителю.")
        return

    await query.answer()

    context.user_data['category'] = query.data
    await query.message.edit_text("Пожалуйста, отправьте чек.")
    return SENDING_RECEIPT


async def send_receipt(update: Update, context: CallbackContext) -> int:
    if update.message.photo:
        logger.info("Фото получено, начинается обработка...")

        try:
            photo_file = await context.bot.get_file(update.message.photo[-1].file_id)
            local_path = f"{photo_file.file_id}.jpg"
            await photo_file.download_to_drive(local_path)

            logger.info("Фото успешно получено и обработано.")

            # Генерация уникального идентификатора для чека
            unique_id = str(uuid.uuid4())

            # Отправка фото в группу
            caption = f"Чек №{unique_id}"

            try:
                with open(local_path, 'rb') as file:
                    await context.bot.send_photo(chat_id=PHOTO_GROUP_CHAT_ID, photo=file, caption=caption)
                logger.info("Фото успешно отправлено в группу.")
            except BadRequest as e:
                logger.error(f"Не удалось отправить фото в группу. Ошибка: {e}")
                await update.message.reply_text(
                    "Ошибка отправки чека в группу. Пожалуйста, убедитесь, что бот добавлен в группу."
                )
                return SENDING_RECEIPT

            # Сохранение порядкового номера фото в user_data
            context.user_data['photo_number'] = unique_id

            # Удаление локального файла асинхронно с помощью asyncio.to_thread
            try:
                await asyncio.to_thread(os.remove, local_path)
                logger.info(f"Файл {local_path} успешно удалён.")
            except Exception as e:
                logger.error(f"Не удалось удалить файл: {local_path}. Ошибка: {e}")

            await update.message.reply_text("Чек успешно получен. Теперь отправьте наименование покупки (например: бананы)")
            return GET_NAME

        except Exception as e:
            logger.error(f"Ошибка при загрузке или отправке фото: {e}")
            await update.message.reply_text(
                "Произошла ошибка при обработке вашего фото. Пожалуйста, попробуйте еще раз.")
            return SENDING_RECEIPT
    else:
        await update.message.reply_text("Пожалуйста, отправьте фото чека.")
        return SENDING_RECEIPT

async def get_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Спасибо! Теперь отправьте сумму покупки (например: 1000 руб)")
    return GET_AMOUNT

async def get_amount(update: Update, context: CallbackContext) -> int:
    context.user_data['amount'] = update.message.text
    await update.message.reply_text("Спасибо! Теперь отправьте место покупки (например: супермаркет)")
    return GET_PLACE

async def get_place(update: Update, context: CallbackContext) -> int:
    context.user_data['place'] = update.message.text
    await update.message.reply_text("Спасибо! Теперь отправьте дату покупки (например: 18.10.2024)")
    return GET_DATE

async def get_date(update: Update, context: CallbackContext) -> int:
    context.user_data['date'] = update.message.text
    category = context.user_data.get('category', 'Категория не выбрана')
    photo_number = context.user_data.get('photo_number', 'Фото не предоставлено')
    user_name = update.message.from_user.username
    name = context.user_data.get('name')
    amount = context.user_data.get('amount')
    place = context.user_data.get('place')
    date = context.user_data.get('date')

    try:
        await asyncio.to_thread(
            sheet.append_row, [user_name, category, name, date, amount, place, f"Чек №{photo_number}"]
        )
    except Exception as e:
        logger.error(f"Ошибка при добавлении данных в Google Sheets: {e}")
        await update.message.reply_text("Ошибка при добавлении данных в Google Sheets. Пожалуйста, попробуйте еще раз.")
        return SENDING_RECEIPT

    context.user_data.clear()
    categories = load_categories()  # Загружаем категории
    category_buttons = [[InlineKeyboardButton(category, callback_data=category)] for category in categories]

    await update.message.reply_text(
        "Добро пожаловать, ассистент! Пожалуйста, выберите категорию расходов:",
        reply_markup=InlineKeyboardMarkup(category_buttons)
    )

    return CHOOSING_CATEGORY

async def check_state(update: Update, context: CallbackContext) -> None:
    current_state = context.user_data.get('state', 'не определено')
    await update.message.reply_text(f"Текущее состояние: {current_state}")
