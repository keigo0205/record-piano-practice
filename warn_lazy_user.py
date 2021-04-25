# -*- coding: utf-8 -*-
import psycopg2
import os
from linebot import LineBotApi
from linebot.models import TextSendMessage
from datetime import datetime, timedelta

DATABASE_URL = os.environ['DATABASE_URL']
DB_NAME = "test_table"


def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')


def getUserPractice():
    sql = "SELECT * from " + DB_NAME
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            results = cur.fetchall()
    return results


if __name__ == "__main__":
    print("Started: warn_lazy_user.py")
    user_practice = getUserPractice()
    lazy_users = {}
    for user, _, time in user_practice:
        if user not in lazy_users:
            lazy_users[user] = time
        else:
            lazy_users[user] = max(lazy_users[user], time)

    channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
    line_bot_api = LineBotApi(channel_access_token)
    now = datetime.now()
    base_delta = timedelta(seconds=24)
    base_text = "最後に練習してから24時間以上経過しています。\n"
    base_text += "最後に練習した時間は "
    for user, time in lazy_users.items():
        no_practice_time = now - time
        if base_delta < no_practice_time:
            line_bot_api.push_message(
                user,
                TextSendMessage(base_text + str(time) + "です。")
            )
    print("Completed: warn_lazy_user.py")
