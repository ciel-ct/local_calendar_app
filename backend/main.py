import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

app = FastAPI()

# 💡 ローカル環境でVue（ポート5173）から通信できるようにCORSを設定するよっ
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 個人用カレンダーID
CALENDAR_ID = os.getenv("CALENDAR_ID", "")
# # Google公式の日本祝日ID
HOLIDAY_CALENDAR_ID = 'ja.japanese.official#holiday@group.v.calendar.google.com'
# Google公式の日本祝日ID (行事付き)
# HOLIDAY_CALENDAR_ID = 'ja.japanese#holiday@group.v.calendar.google.com'
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

@app.get("/api/events")
def get_calendar_events(start: str, end: str):
    try:
        # サービスアカウントの鍵を使ってGoogleの認証を受けるよ！
        creds = service_account.Credentials.from_service_account_file(
            'credentials.json', scopes=SCOPES
        )
        service = build('calendar', 'v3', credentials=creds)

        # の予定を取得
        events_result = service.events().list(
            calendarId=CALENDAR_ID, timeMin=start, timeMax=end, singleEvents=True, orderBy='startTime'
        ).execute()
        my_events = events_result.get('items', [])

        # 日本の祝日を取得（これは一般公開なのでサービスアカウントでそのまま取れます！）
        holidays_result = service.events().list(
            calendarId=HOLIDAY_CALENDAR_ID, timeMin=start, timeMax=end, singleEvents=True
        ).execute()
        holiday_events = holidays_result.get('items', [])
        
        # 祝日データには「isHoliday: true」という目印（タグ）をつけて合体させる！
        for holiday in holiday_events:
            holiday['isHoliday'] = True

        events = my_events + holiday_events

        return {"status": "success", "data": events}
        
    except Exception as e:
        print("--- エラーの詳細 ---", str(e))

        return {"status": "error", "message": str(e)}