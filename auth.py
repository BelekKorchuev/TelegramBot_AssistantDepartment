from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
from head_assistant import load_assistants, view_requests, load_categories
from constants_and_google import MANAGER_USERNAME, MANAGER_PASSWORD, CHOOSING_ROLE, MANAGER_LOGIN, MANAGER_OPTIONS, \
    CHOOSING_CATEGORY


async def start(update: Update, context: CallbackContext) -> int:
    context.user_data.clear()
    reply_keyboard = [[KeyboardButton("Руководитель"), KeyboardButton("Ассистент")]]

    await update.message.reply_text(
        "Добро пожаловать! Пожалуйста, выберите свою роль:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING_ROLE


async def choose_role(update: Update, context: CallbackContext) -> int:
    user_choice = update.message.text
    if user_choice == "Руководитель":
        await update.message.reply_text("Пожалуйста, введите логин:")
        return MANAGER_LOGIN
    elif user_choice == "Ассистент":
        user_id = update.message.from_user.id
        authorized_assistants = load_assistants()
        if str(user_id) in authorized_assistants:
            categories = load_categories()  # Загружаем категории
            # Динамически создаем кнопки категорий из общего списка категорий
            category_buttons = [[InlineKeyboardButton(category, callback_data=category)] for category in categories]

            await update.message.reply_text(
                "Добро пожаловать, ассистент! Пожалуйста, выберите категорию расходов:",
                reply_markup=InlineKeyboardMarkup(category_buttons)
            )
            return CHOOSING_CATEGORY
        else:
            reply_keyboard = [
                [InlineKeyboardButton("Отправить запрос на доступ", callback_data=f'request_access_{user_id}')]
            ]
            await update.message.reply_text(
                "Извините, у вас нет доступа к системе. Вы можете отправить запрос на доступ.",
                reply_markup=InlineKeyboardMarkup(reply_keyboard)
            )
            return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, выберите действительную роль.")
        return CHOOSING_ROLE


async def manager_login(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    if "username" not in context.user_data:
        context.user_data["username"] = text
        await update.message.reply_text("Пожалуйста, введите пароль:")
        return MANAGER_LOGIN
    else:
        if context.user_data["username"] == MANAGER_USERNAME and text == MANAGER_PASSWORD:
            reply_keyboard = [
                [InlineKeyboardButton("Просмотр запросов", callback_data='view_requests')],
                [InlineKeyboardButton("Просмотреть список ассистентов", callback_data='view_assistants')],
                [InlineKeyboardButton("Удалить ассистента", callback_data='delete_assistant')],
                [InlineKeyboardButton("Отчет", callback_data='report')],
                [InlineKeyboardButton("Отчет в чат", callback_data='chat_report')],
                [InlineKeyboardButton("Ссылка на группу с чеками", callback_data='group_link')],
                [InlineKeyboardButton("Ссылка на таблицу", callback_data='table_link')],
                [InlineKeyboardButton("Добавить категорию", callback_data='add_category'),
                 InlineKeyboardButton("Удалить категорию", callback_data='remove_category')]
            ]
            await update.message.reply_text(
                "Добро пожаловать, руководитель! Вы можете просматривать отчеты и управлять ассистентами.",
                reply_markup=InlineKeyboardMarkup(reply_keyboard)
            )

            chat_id = update.message.chat_id
            await view_requests(context, chat_id)  # Используем view_requests здесь

            return MANAGER_OPTIONS
        else:
            await update.message.reply_text("Неправильный логин или пароль. Попробуйте снова.")
            context.user_data.clear()
            return await start(update, context)


async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Авторизация отменена.")
    return ConversationHandler.END
