import json
import os
from datetime import datetime
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackContext
from constants_and_google import MANAGER_OPTIONS, client, GET_REPORT_PERIOD, GoogleSheetsLink, ADD_CATEGORY, \
    REMOVE_CATEGORY, CHOOSE_COLUMNS, ADD_REPORT_PERIOD

ASSISTANTS_FILE = "assistants.json"

# Список для хранения запросов от ассистентов
pending_requests = []


def load_assistants():
    try:
        with open(ASSISTANTS_FILE, "r") as file:
            data = json.load(file)
            return data.get("authorized_assistants", {})
    except FileNotFoundError:
        return {}


def save_assistants(assistants):
    with open(ASSISTANTS_FILE, "w") as file:
        json.dump({"authorized_assistants": assistants}, file)


async def manager_options(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "view_assistants":
        await view_assistants(update, context)

        # Показать список возможностей руководителя снова
        reply_keyboard = [
            [InlineKeyboardButton("Просмотр запросов", callback_data='view_requests')],
            [InlineKeyboardButton("Просмотреть список ассистентов",
                                  callback_data='view_assistants')],
            [InlineKeyboardButton("Удалить ассистента",
                                  callback_data='delete_assistant')],
            [InlineKeyboardButton("Отчет", callback_data='report')],
            [InlineKeyboardButton("Отчет в чат", callback_data='chat_report')],
            [InlineKeyboardButton("Ссылка на группу с чеками",
                                  callback_data='group_link')],
            [InlineKeyboardButton("Ссылка на таблицу", callback_data='table_link')],
            [InlineKeyboardButton("Добавить категорию", callback_data='add_category'),
             InlineKeyboardButton("Удалить категорию", callback_data='remove_category')]
        ]
        await query.message.reply_text(
            "Что вы хотите сделать дальше?",
            reply_markup=InlineKeyboardMarkup(reply_keyboard)
        )

    elif choice == "view_requests":
        await view_requests(context, query.message.chat_id)

    elif choice == "delete_assistant":
        await delete_assistant(update, context)

    elif choice == "group_link":
        await query.message.reply_text("Ссылка на группу с чеками: https://t.me/+SCCpmDGmqLo5Njky")
        # Показать список возможностей руководителя снова
        reply_keyboard = [
            [InlineKeyboardButton("Просмотр запросов", callback_data='view_requests')],
            [InlineKeyboardButton("Просмотреть список ассистентов",
                                  callback_data='view_assistants')],
            [InlineKeyboardButton("Удалить ассистента",
                                  callback_data='delete_assistant')],
            [InlineKeyboardButton("Отчет", callback_data='report')],
            [InlineKeyboardButton("Отчет в чат", callback_data='chat_report')],
            [InlineKeyboardButton("Ссылка на группу с чеками",
                                  callback_data='group_link')],
            [InlineKeyboardButton("Ссылка на таблицу", callback_data='table_link')],
            [InlineKeyboardButton("Добавить категорию", callback_data='add_category'),
             InlineKeyboardButton("Удалить категорию", callback_data='remove_category')]
        ]
        await query.message.reply_text(
            "Что вы хотите сделать дальше?",
            reply_markup=InlineKeyboardMarkup(reply_keyboard)
        )
    elif choice == "report":
        await query.message.reply_text("Пожалуйста, укажите период для отчета в формате 'с ДД.ММ.ГГГГ по ДД.ММ.ГГГГ'.")
        return GET_REPORT_PERIOD

    elif choice == "chat_report":
        await choose_report_columns(update, context)
        return CHOOSE_COLUMNS

    elif choice == "table_link":
        await query.message.reply_text(f"[Ссылка на Google Таблицы]({GoogleSheetsLink})", parse_mode=ParseMode.MARKDOWN_V2)
        # Показать список возможностей руководителя снова
        reply_keyboard = [
            [InlineKeyboardButton("Просмотр запросов", callback_data='view_requests')],
            [InlineKeyboardButton("Просмотреть список ассистентов",
                                  callback_data='view_assistants')],
            [InlineKeyboardButton("Удалить ассистента",
                                  callback_data='delete_assistant')],
            [InlineKeyboardButton("Отчет", callback_data='report')],
            [InlineKeyboardButton("Отчет в чат", callback_data='chat_report')],
            [InlineKeyboardButton("Ссылка на группу с чеками",
                                  callback_data='group_link')],
            [InlineKeyboardButton("Ссылка на таблицу", callback_data='table_link')],
            [InlineKeyboardButton("Добавить категорию", callback_data='add_category'),
             InlineKeyboardButton("Удалить категорию", callback_data='remove_category')]
        ]
        await query.message.reply_text(
            "Что вы хотите сделать дальше?",
            reply_markup=InlineKeyboardMarkup(reply_keyboard)
        )

    elif choice == "add_category":
        await add_category(update, context)
        return ADD_CATEGORY

    elif choice == "remove_category":
        await remove_category(update, context)
        return REMOVE_CATEGORY

    return MANAGER_OPTIONS


async def request_access(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = int(query.data.split('_')[-1])
    user_name = query.from_user.username or "Имя не указано"
    await query.answer()

    print(query)
    # Добавляем запрос в очередь с id и никнеймом
    if user_id not in [request[0] for request in pending_requests]:
        pending_requests.append((user_id, user_name))

    # Добавляем запрос в очередь и выводим сообщение
    print(f"Добавлен запрос на доступ от пользователя с ID {user_id} и никнеймом @{user_name}")


async def confirm_assistant(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = int(query.data.split('_')[-1])  # Извлечение user_id из callback_data
    user_request = next((req for req in pending_requests if req[0] == user_id), None)

    if not user_request:
        await query.answer("Запрос не найден.")
        return

    user_name = user_request[1]

    await query.answer()

    if any(request[0] == user_id for request in pending_requests):
        assistants = load_assistants()
        if str(user_id) not in assistants:
            assistants[str(user_id)] = user_name
            save_assistants(assistants)
            pending_requests.remove((user_id, user_name))

            await query.edit_message_text(f"Новый ассистент с ID {user_id} был добавлен.", reply_markup=None)

            # Показать список возможностей руководителя снова
            reply_keyboard = [
                [InlineKeyboardButton("Просмотр запросов", callback_data='view_requests')],
                [InlineKeyboardButton("Просмотреть список ассистентов",
                                      callback_data='view_assistants')],
                [InlineKeyboardButton("Удалить ассистента",
                                      callback_data='delete_assistant')],
                [InlineKeyboardButton("Отчет", callback_data='report')],
                [InlineKeyboardButton("Отчет в чат", callback_data='chat_report')],
                [InlineKeyboardButton("Ссылка на группу с чеками",
                                      callback_data='group_link')],
                [InlineKeyboardButton("Ссылка на таблицу", callback_data='table_link')],
                [InlineKeyboardButton("Добавить категорию", callback_data='add_category'),
                 InlineKeyboardButton("Удалить категорию", callback_data='remove_category')]
            ]
            await query.message.reply_text(
                "Что вы хотите сделать дальше?",
                reply_markup=InlineKeyboardMarkup(reply_keyboard)
            )

            try:

                await context.bot.send_message(
                    chat_id=user_id,
                    text="Ваш запрос на доступ был одобрен! Теперь у вас есть доступ к системе.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('Транспорт', callback_data='Транспорт')],
                        [InlineKeyboardButton('Питание', callback_data='Питание')],
                        [InlineKeyboardButton('Офисные расходы', callback_data='Офисные расходы')],
                        [InlineKeyboardButton('Другое', callback_data='Другое')]
                    ])
                )
            except Exception as e:
                print(f"Ошибка отправки сообщения новому ассистенту: {e}")
        else:
            await query.edit_message_text(f"Ассистент с ID {user_id} уже существует.")
    else:
        await query.edit_message_text(f"Запрос на добавление ассистента с ID {user_id} не найден.")


async def reject_assistant(update: Update, context: CallbackContext) -> None:
    global pending_requests

    query = update.callback_query
    user_id = int(query.data.split('_')[-1])  # Извлечение user_id из callback_data

    await query.answer()

    if any(request[0] == user_id for request in pending_requests):
        pending_requests = [req for req in pending_requests if req[0] != user_id]
        await query.edit_message_text(f"Запрос на добавление ассистента с ID {user_id} был отклонен.")

        # Показать список возможностей руководителя снова
        reply_keyboard = [
            [InlineKeyboardButton("Просмотр запросов", callback_data='view_requests')],
            [InlineKeyboardButton("Просмотреть список ассистентов",
                                  callback_data='view_assistants')],
            [InlineKeyboardButton("Удалить ассистента",
                                  callback_data='delete_assistant')],
            [InlineKeyboardButton("Отчет", callback_data='report')],
            [InlineKeyboardButton("Отчет в чат", callback_data='chat_report')],
            [InlineKeyboardButton("Ссылка на группу с чеками",
                                  callback_data='group_link')],
            [InlineKeyboardButton("Ссылка на таблицу", callback_data='table_link')],
            [InlineKeyboardButton("Добавить категорию", callback_data='add_category'),
             InlineKeyboardButton("Удалить категорию", callback_data='remove_category')]
        ]
        await query.message.reply_text(
            "Что вы хотите сделать дальше?",
            reply_markup=InlineKeyboardMarkup(reply_keyboard)
        )

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="Ваш запрос на доступ был отклонен. Пожалуйста, свяжитесь с руководителем для получения дополнительной информации."
            )
        except Exception as e:
            print(f"Ошибка отправки сообщения об отказе ассистенту: {e}")
    else:
        await query.edit_message_text(f"Запрос на добавление ассистента с ID {user_id} не найден.")


async def view_requests(context: CallbackContext, chat_id: int) -> None:
    if not pending_requests:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Нет запросов на добавление ассистентов."
        )
        return
    for user_id, user_name in pending_requests:
        reply_keyboard = [
            [InlineKeyboardButton("Принять", callback_data=f'confirm_{user_id}')],
            [InlineKeyboardButton("Отклонить", callback_data=f'reject_{user_id}')],
        ]

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Запрос на добавление ассистента с ID {user_id}, Никнейм: @{user_name}",
            reply_markup=InlineKeyboardMarkup(reply_keyboard)
        )


async def view_assistants(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    assistants = load_assistants()
    assistants_list = "\n".join([f"Ник: @{name} - id: {assistant}" for assistant, name in assistants.items()])
    if assistants_list:
        await query.message.reply_text(f"Список ассистентов:\n{assistants_list}")
    else:
        await query.message.reply_text("Список ассистентов пуст.")


async def delete_assistant(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    assistants = load_assistants()

    if not assistants:
        await query.message.reply_text("Нет ассистентов для удаления.")
        return

    # Создаем кнопки для каждого ассистента, чтобы удалить его
    reply_keyboard = [
        [InlineKeyboardButton(f"Удалить ассистента @{name} - ID {assistant}", callback_data=f'delete_{assistant}')]
        for assistant, name in assistants.items()
    ]
    await query.message.reply_text(
        "Выберите ассистента для удаления:",
        reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )


async def confirm_delete_assistant(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    callback_data = query.data
    print(f"Получены данные для удаления: {query.data}")

    try:
        if not callback_data.startswith("delete_"):
            await query.answer("Некорректные данные для удаления.")
            print("Некорректные данные для удаления")
            return
        user_id = callback_data.split('_')[-1]
        print(f"ID ассистента для удаления: {user_id}")

    except ValueError:
        await query.answer("Ошибка: некорректный формат данных для удаления.")
        return

    await query.answer()

    assistants = load_assistants()
    if user_id in assistants:
        user_name = assistants[user_id]
        del assistants[user_id]  # Удаляем ассистента из словаря
        save_assistants(assistants)
        await query.edit_message_text(f"Ассистент @{user_name} - ID {user_id} был удален.")

        # Показать список возможностей руководителя снова
        reply_keyboard = [
            [InlineKeyboardButton("Просмотр запросов", callback_data='view_requests')],
            [InlineKeyboardButton("Просмотреть список ассистентов",
                                  callback_data='view_assistants')],
            [InlineKeyboardButton("Удалить ассистента",
                                  callback_data='delete_assistant')],
            [InlineKeyboardButton("Отчет", callback_data='report')],
            [InlineKeyboardButton("Отчет в чат", callback_data='chat_report')],
            [InlineKeyboardButton("Ссылка на группу с чеками",
                                  callback_data='group_link')],
            [InlineKeyboardButton("Ссылка на таблицу", callback_data='table_link')],
            [InlineKeyboardButton("Добавить категорию", callback_data='add_category'),
             InlineKeyboardButton("Удалить категорию", callback_data='remove_category')]
        ]
        await query.message.reply_text(
            "Что вы хотите сделать дальше?",
            reply_markup=InlineKeyboardMarkup(reply_keyboard)
        )
    else:
        await query.edit_message_text(f"Ассистент с ID {user_id} не найден.")

        # Показать список возможностей руководителя снова
        reply_keyboard = [
            [InlineKeyboardButton("Просмотр запросов", callback_data='view_requests')],
            [InlineKeyboardButton("Просмотреть список ассистентов", callback_data='view_assistants')],
            [InlineKeyboardButton("Удалить ассистента", callback_data='delete_assistant')],
            [InlineKeyboardButton("Отчет", callback_data='report')],
            [InlineKeyboardButton("Ссылка на группу с чеками", callback_data='group_link')],
            [InlineKeyboardButton("Ссылка на таблицу", callback_data='table_link')],
            [InlineKeyboardButton("Добавить категорию", callback_data='add_category'),
             InlineKeyboardButton("Удалить категорию", callback_data='remove_category')]
        ]
        await query.message.reply_text(
            "Что вы хотите сделать дальше?",
            reply_markup=InlineKeyboardMarkup(reply_keyboard)
        )


CATEGORIES_FILE = "categories.json"


def load_categories():
    try:
        with open(CATEGORIES_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("categories", ["Транспорт", "Питание", "Офисные расходы", "Другое"])
    except FileNotFoundError:
        return ["Транспорт", "Питание", "Офисные расходы", "Другое"]


def save_categories(categories):
    with open(CATEGORIES_FILE, "w", encoding="utf-8") as file:
        json.dump({"categories": list(categories)}, file, ensure_ascii=False)


async def add_category(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.message.reply_text("Пожалуйста, введите название новой категории:")
    return ADD_CATEGORY


# Функция сохранения новой категории
async def save_new_category(update: Update, context: CallbackContext) -> int:
    categories = load_categories()  # Загружаем категории
    new_category = update.message.text.strip()
    if new_category in categories:
        await update.message.reply_text(f"Категория '{new_category}' уже существует.")
    else:
        categories.append(new_category)
        save_categories(categories)  # Сохраняем категории в файл
        await update.message.reply_text(f"Категория '{new_category}' успешно добавлена.")

    # Возвращаемся в меню руководителя
    reply_keyboard = [
        [InlineKeyboardButton("Просмотр запросов", callback_data='view_requests')],
        [InlineKeyboardButton("Просмотреть список ассистентов",
                              callback_data='view_assistants')],
        [InlineKeyboardButton("Удалить ассистента",
                              callback_data='delete_assistant')],
        [InlineKeyboardButton("Отчет", callback_data='report')],
        [InlineKeyboardButton("Отчет в чат", callback_data='chat_report')],
        [InlineKeyboardButton("Ссылка на группу с чеками",
                              callback_data='group_link')],
        [InlineKeyboardButton("Ссылка на таблицу", callback_data='table_link')],
        [InlineKeyboardButton("Добавить категорию", callback_data='add_category'),
         InlineKeyboardButton("Удалить категорию", callback_data='remove_category')]
    ]
    await update.message.reply_text(
        "Что вы хотите сделать дальше?",
        reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )

    return MANAGER_OPTIONS


async def remove_category(update: Update, context: CallbackContext) -> int:
    categories = load_categories()  # Загружаем категории
    query = update.callback_query
    await query.answer()
    # Создаем кнопки категорий из текущего списка категорий
    category_buttons = [[InlineKeyboardButton(category, callback_data=f'remove_{category}')] for category in categories]
    # Отправляем сообщение с кнопками, чтобы руководитель выбрал категорию для удаления
    await query.message.edit_text(
        "Пожалуйста, выберите категорию, которую вы хотите удалить:",
        reply_markup=InlineKeyboardMarkup(category_buttons)
    )

    return REMOVE_CATEGORY


async def confirm_remove_category(update: Update, context: CallbackContext) -> int:
    categories = load_categories()  # Загружаем категории
    query = update.callback_query
    print(query)
    category_to_remove = query.data.replace("remove_", "")
    await query.answer()
    # Удаляем выбранную категорию, если она существует в списке
    if category_to_remove in categories:
        categories.remove(category_to_remove)
        save_categories(categories)  # Сохраняем изменения в файл
        await query.message.edit_text(f"Категория '{category_to_remove}' успешно удалена.")
    else:
        await query.answer("Категория не найдена.")

    # Возвращаемся в меню руководителя
    reply_keyboard = [
        [InlineKeyboardButton("Просмотр запросов", callback_data='view_requests')],
        [InlineKeyboardButton("Просмотреть список ассистентов",
                              callback_data='view_assistants')],
        [InlineKeyboardButton("Удалить ассистента",
                              callback_data='delete_assistant')],
        [InlineKeyboardButton("Отчет", callback_data='report')],
        [InlineKeyboardButton("Отчет в чат", callback_data='chat_report')],
        [InlineKeyboardButton("Ссылка на группу с чеками",
                              callback_data='group_link')],
        [InlineKeyboardButton("Ссылка на таблицу", callback_data='table_link')],
        [InlineKeyboardButton("Добавить категорию", callback_data='add_category'),
         InlineKeyboardButton("Удалить категорию", callback_data='remove_category')]
    ]
    await query.message.reply_text(
        "Что вы хотите сделать дальше?",
        reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )

    return MANAGER_OPTIONS


async def get_group_id(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"ID этой группы: {chat_id}")


async def get_report_period(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text

    # Парсим даты из строки
    try:
        start_date_str, end_date_str = user_input.lower().replace("с ", "").replace("по ", "").split(" ")
        start_date = datetime.strptime(start_date_str.strip(), "%d.%m.%Y")
        end_date = datetime.strptime(end_date_str.strip(), "%d.%m.%Y")
    except ValueError:
        await update.message.reply_text(
            "Некорректный формат. Пожалуйста, укажите даты в формате 'с ДД.ММ.ГГГГ по ДД.ММ.ГГГГ'.")
        return GET_REPORT_PERIOD

        # Получаем данные из Google Sheets (предполагается, что данные уже загружены в DataFrame)
    try:
        # Получаем данные из Google Sheets (предполагается, что данные уже загружены в DataFrame)
        sheet = client.open("Отчеты в отделе ассистентов").sheet1
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
    except Exception as e:
        await update.message.reply_text(
            f"Не удалось подключиться к Google Sheets. Пожалуйста, попробуйте позже. Ошибка: {str(e)}"
        )
        await update.message.reply_text("Что вы хотите сделать дальше?",
                                        reply_markup=InlineKeyboardMarkup([
                                            [InlineKeyboardButton("Просмотр запросов", callback_data='view_requests')],
                                            [InlineKeyboardButton("Просмотреть список ассистентов",
                                                                  callback_data='view_assistants')],
                                            [InlineKeyboardButton("Удалить ассистента",
                                                                  callback_data='delete_assistant')],
                                            [InlineKeyboardButton("Отчет", callback_data='report')],
                                            [InlineKeyboardButton("Отчет в чат", callback_data='chat_report')],
                                            [InlineKeyboardButton("Ссылка на группу с чеками",
                                                                  callback_data='group_link')],
                                            [InlineKeyboardButton("Ссылка на таблицу", callback_data='table_link')],
                                            [InlineKeyboardButton("Добавить категорию", callback_data='add_category'),
                                             InlineKeyboardButton("Удалить категорию", callback_data='remove_category')]
                                        ]))
        return MANAGER_OPTIONS

    # Печать списка столбцов для отладки
    print(f"Доступные столбцы: {df.columns.tolist()}")

    if 'Дата' not in df.columns:
        await update.message.reply_text(
            "Ошибка: Столбец 'Дата' не найден. Пожалуйста, убедитесь, что Google Sheet содержит этот столбец.")
        # Возвращаемся в меню руководителя
        await update.message.reply_text("Что вы хотите сделать дальше?",
                                        reply_markup=InlineKeyboardMarkup([
                                            [InlineKeyboardButton("Просмотр запросов", callback_data='view_requests')],
                                            [InlineKeyboardButton("Просмотреть список ассистентов",
                                                                  callback_data='view_assistants')],
                                            [InlineKeyboardButton("Удалить ассистента",
                                                                  callback_data='delete_assistant')],
                                            [InlineKeyboardButton("Отчет", callback_data='report')],
                                            [InlineKeyboardButton("Отчет в чат", callback_data='chat_report')],
                                            [InlineKeyboardButton("Ссылка на группу с чеками",
                                                                  callback_data='group_link')],
                                            [InlineKeyboardButton("Ссылка на таблицу", callback_data='table_link')],
                                            [InlineKeyboardButton("Добавить категорию", callback_data='add_category'),
                                             InlineKeyboardButton("Удалить категорию", callback_data='remove_category')]
                                        ]))
        return MANAGER_OPTIONS

    # Преобразуем дату в формат datetime для фильтрации
    df['Дата'] = pd.to_datetime(df['Дата'], format='%d.%m.%Y', errors='coerce')

    # Фильтруем по диапазону дат
    filtered_df = df[(df['Дата'] >= start_date) & (df['Дата'] <= end_date)]

    # Проверяем, есть ли данные за указанный период
    if filtered_df.empty:
        await update.message.reply_text(
            "Нет данных за указанный период. Пожалуйста, попробуйте другой диапазон дат.")
        # Возвращаемся в меню руководителя
        await update.message.reply_text("Что вы хотите сделать дальше?",
                                        reply_markup=InlineKeyboardMarkup([
                                            [InlineKeyboardButton("Просмотр запросов", callback_data='view_requests')],
                                            [InlineKeyboardButton("Просмотреть список ассистентов",
                                                                  callback_data='view_assistants')],
                                            [InlineKeyboardButton("Удалить ассистента",
                                                                  callback_data='delete_assistant')],
                                            [InlineKeyboardButton("Отчет", callback_data='report')],
                                            [InlineKeyboardButton("Отчет в чат", callback_data='chat_report')],
                                            [InlineKeyboardButton("Ссылка на группу с чеками",
                                                                  callback_data='group_link')],
                                            [InlineKeyboardButton("Ссылка на таблицу", callback_data='table_link')],
                                            [InlineKeyboardButton("Добавить категорию", callback_data='add_category'),
                                             InlineKeyboardButton("Удалить категорию", callback_data='remove_category')]
                                        ]))
        return GET_REPORT_PERIOD

    # Создаем Excel файл с результатами
    report_file_path = "Отчет.xlsx"
    filtered_df.to_excel(report_file_path, index=False)

    # Отправляем файл руководителю
    await context.bot.send_document(chat_id=update.message.chat_id, document=open(report_file_path, 'rb'))

    # Удаляем файл после отправки (по желанию)
    os.remove(report_file_path)

    # Возвращаемся в меню руководителя
    await update.message.reply_text("Отчет отправлен. Что вы хотите сделать дальше?",
                                    reply_markup=InlineKeyboardMarkup([
                                        [InlineKeyboardButton("Просмотр запросов", callback_data='view_requests')],
                                        [InlineKeyboardButton("Просмотреть список ассистентов",
                                                              callback_data='view_assistants')],
                                        [InlineKeyboardButton("Удалить ассистента",
                                                              callback_data='delete_assistant')],
                                        [InlineKeyboardButton("Отчет", callback_data='report')],
                                        [InlineKeyboardButton("Отчет в чат", callback_data='chat_report')],
                                        [InlineKeyboardButton("Ссылка на группу с чеками",
                                                              callback_data='group_link')],
                                        [InlineKeyboardButton("Ссылка на таблицу", callback_data='table_link')],
                                        [InlineKeyboardButton("Добавить категорию", callback_data='add_category'),
                                         InlineKeyboardButton("Удалить категорию", callback_data='remove_category')]
                                    ]))
    return MANAGER_OPTIONS


async def choose_report_columns(update: Update, context: CallbackContext) -> int:
    columns = ["Ассистент", "Категория", "Объект или услуга", "Дата", "Сумма", "Место покупки", "Номер чека"]
    context.user_data['columns'] = []

    column_buttons = [[InlineKeyboardButton(column, callback_data=f'column_{column}')] for column in columns]
    column_buttons.append([InlineKeyboardButton("Продолжить>>", callback_data='continue_report')])

    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "Пожалуйста, выберите колонки для отчета (нажмите на нужные, затем 'Продолжить'):",
        reply_markup=InlineKeyboardMarkup(column_buttons)
    )
    return CHOOSE_COLUMNS


async def add_report_column(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    column = query.data.replace("column_", "")

    # Добавляем колонку, если она еще не выбрана
    if column not in context.user_data['columns']:
        context.user_data['columns'].append(column)
        await query.answer(f"Колонка '{column}' добавлена")
    else:
        await query.answer(f"Колонка '{column}' уже выбрана")

    return CHOOSE_COLUMNS


async def choose_report_period(update: Update, context: CallbackContext) -> int:
    await update.callback_query.message.edit_text(
        "Пожалуйста, укажите период для отчета в формате 'с ДД.ММ.ГГГГ по ДД.ММ.ГГГГ':"
    )
    return ADD_REPORT_PERIOD


async def generate_report_to_chat(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    try:
        start_date_str, end_date_str = user_input.lower().replace("с ", "").replace("по ", "").split(" ")
        start_date = datetime.strptime(start_date_str.strip(), "%d.%m.%Y")
        end_date = datetime.strptime(end_date_str.strip(), "%d.%m.%Y")
    except ValueError:
        await update.message.reply_text(
            "Некорректный формат. Пожалуйста, укажите даты в формате 'с ДД.ММ.ГГГГ по ДД.ММ.ГГГГ'."
        )
        return ADD_REPORT_PERIOD

    # Получаем данные из Google Sheets (предполагается, что данные уже загружены в DataFrame)
    try:
        # Получаем данные из Google Sheets (предполагается, что данные уже загружены в DataFrame)
        sheet = client.open("Отчеты в отделе ассистентов").sheet1
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
    except Exception as e:
        await update.message.reply_text(
            f"Не удалось подключиться к Google Sheets. Пожалуйста, попробуйте позже. Ошибка: {str(e)}"
        )
        await update.message.reply_text("Что вы хотите сделать дальше?",
                                        reply_markup=InlineKeyboardMarkup([
                                            [InlineKeyboardButton("Просмотр запросов", callback_data='view_requests')],
                                            [InlineKeyboardButton("Просмотреть список ассистентов",
                                                                  callback_data='view_assistants')],
                                            [InlineKeyboardButton("Удалить ассистента",
                                                                  callback_data='delete_assistant')],
                                            [InlineKeyboardButton("Отчет", callback_data='report')],
                                            [InlineKeyboardButton("Отчет в чат", callback_data='chat_report')],
                                            [InlineKeyboardButton("Ссылка на группу с чеками",
                                                                  callback_data='group_link')],
                                            [InlineKeyboardButton("Ссылка на таблицу", callback_data='table_link')],
                                            [InlineKeyboardButton("Добавить категорию", callback_data='add_category'),
                                             InlineKeyboardButton("Удалить категорию", callback_data='remove_category')]
                                        ]))
        return MANAGER_OPTIONS

    # Фильтруем данные по выбранному периоду
    df['Дата'] = pd.to_datetime(df['Дата'], format='%d.%m.%Y', errors='coerce')
    filtered_df = df[(df['Дата'] >= start_date) & (df['Дата'] <= end_date)]

    # Оставляем только выбранные колонки
    selected_columns = context.user_data.get('columns', [])
    if not selected_columns:
        await update.message.reply_text("Вы не выбрали ни одной колонки для отчета.")
        await update.message.reply_text("Что вы хотите сделать дальше?",
                                        reply_markup=InlineKeyboardMarkup([
                                            [InlineKeyboardButton("Просмотр запросов", callback_data='view_requests')],
                                            [InlineKeyboardButton("Просмотреть список ассистентов",
                                                                  callback_data='view_assistants')],
                                            [InlineKeyboardButton("Удалить ассистента",
                                                                  callback_data='delete_assistant')],
                                            [InlineKeyboardButton("Отчет", callback_data='report')],
                                            [InlineKeyboardButton("Ссылка на группу с чеками",
                                                                  callback_data='group_link')],
                                            [InlineKeyboardButton("Ссылка на таблицу", callback_data='table_link')],
                                            [InlineKeyboardButton("Добавить категорию", callback_data='add_category'),
                                             InlineKeyboardButton("Удалить категорию", callback_data='remove_category')]
                                        ]))
        return MANAGER_OPTIONS

    report_df = filtered_df[selected_columns]

    report_lines = [', '.join(map(str, row)) for row in report_df.values]
    report_text = '\n\n'.join(report_lines)

    report_lines = [
        ", ".join([str(row[col]) for col in selected_columns if col in row])
        for _, row in report_df.iterrows()
    ]
    report_text = "\n\n".join(report_lines)

    # Если выбрана колонка "Сумма", то производим суммирование, но работаем с копией DataFrame
    if 'Сумма' in selected_columns:
        report_df_copy = report_df.copy()
        # Преобразуем значения в колонке "Сумма" в числовой формат
        report_df_copy['Сумма'] = report_df_copy['Сумма'].replace(r'[^\d.]', '', regex=True).apply(pd.to_numeric,
                                                                                                   errors='coerce')
        total_sum = report_df_copy['Сумма'].sum()

        # Добавляем итоговую сумму к тексту отчета
        report_text += f"\n\nИтоговая сумма расходов: {total_sum:.2f} сом"

    # Отправляем отчет в чат
    await update.message.reply_text(
        f"Ваш отчет за период с {start_date_str} по {end_date_str}:\n\n{report_text}"
    )

    # Возвращаемся в меню руководителя
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
        "Что вы хотите сделать дальше?",
        reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )

    return MANAGER_OPTIONS
