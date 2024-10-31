import gspread
from oauth2client.service_account import ServiceAccountCredentials

MANAGER_USERNAME = "admin"
MANAGER_PASSWORD = "password"

(CHOOSING_ROLE, MANAGER_LOGIN, MANAGER_OPTIONS, CHOOSING_CATEGORY, SENDING_RECEIPT, GET_NAME, GET_AMOUNT, GET_PLACE, \
 GET_DATE, GET_REPORT_PERIOD, ADD_CATEGORY, REMOVE_CATEGORY, CHOOSE_COLUMNS, ADD_REPORT_PERIOD) = range(14)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
sheet = client.open("Отчеты в отделе ассистентов").sheet1  # replace with your Google Sheet name

GoogleSheetsLink = "https://docs.google.com/spreadsheets/d/1B8BLuk2jBKFLcKwzFIRFCYlO-cCl4gnBp-zLAQYJsls/edit?usp=sharing"
