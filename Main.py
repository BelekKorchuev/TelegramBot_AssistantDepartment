from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, \
    ConversationHandler, CallbackQueryHandler
from auth import start, choose_role, manager_login, cancel
from assistant import send_receipt, get_name, get_amount, get_place, get_date, \
     choose_category
from head_assistant import manager_options, confirm_assistant, reject_assistant, request_access, \
    confirm_delete_assistant, delete_assistant, get_group_id, get_report_period, save_new_category, \
    confirm_remove_category, generate_report_to_chat, add_report_column, choose_report_columns, choose_report_period
from constants_and_google import CHOOSING_ROLE, MANAGER_LOGIN, MANAGER_OPTIONS, SENDING_RECEIPT, \
    GET_REPORT_PERIOD, GET_NAME, GET_AMOUNT, GET_PLACE, GET_DATE, ADD_CATEGORY, REMOVE_CATEGORY, CHOOSE_COLUMNS, \
    ADD_REPORT_PERIOD, CHOOSING_CATEGORY

if __name__ == "__main__":
    app = ApplicationBuilder().token("7534493156:AAHrlHbYs_oWpYJaax0D3FTtajKsCabtGNQ").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_role)],
            CHOOSING_CATEGORY: [CallbackQueryHandler(choose_category)],
            SENDING_RECEIPT: [MessageHandler(filters.ATTACHMENT, send_receipt)],
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            GET_PLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_place)],
            GET_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            MANAGER_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, manager_login)],
            MANAGER_OPTIONS: [
                CallbackQueryHandler(manager_options,
                                     pattern='^(view_assistants|view_requests|group_link|report|chat_report|table_link|add_category|remove_category)$'),
                CallbackQueryHandler(confirm_assistant, pattern='^confirm_'),
                CallbackQueryHandler(reject_assistant, pattern='^reject_'),
                CallbackQueryHandler(confirm_delete_assistant, pattern='^delete_'),
                CallbackQueryHandler(confirm_remove_category, pattern='^remove_'),
                CallbackQueryHandler(choose_report_columns, pattern='^chat_report$'),
            ],
            CHOOSE_COLUMNS: [
                CallbackQueryHandler(add_report_column, pattern='^column_'),
                CallbackQueryHandler(choose_report_period, pattern='^continue_report$')
            ],
            GET_REPORT_PERIOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_report_period)],
            ADD_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_category)],
            REMOVE_CATEGORY: [CallbackQueryHandler(confirm_remove_category, pattern='^remove_')],
            ADD_REPORT_PERIOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_report_to_chat)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Отдельные обработчики для принятия или отклонения запросов
    app.add_handler(CallbackQueryHandler(request_access, pattern='^request_access_'))
    app.add_handler(CallbackQueryHandler(delete_assistant, pattern='^delete_assistant$'))
    app.add_handler(CommandHandler("get_group_id", get_group_id))
    app.add_handler(conv_handler)
    per_message = True
    app.run_polling()
