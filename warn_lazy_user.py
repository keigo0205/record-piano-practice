# -*- coding: utf-8 -*-
import psycopg2
import os
from linebot import line_bot_api
from linebot.models import TextSendMessage

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

    base_text = "あなたが最後に練習した時間は "
    for user, time in lazy_users.items():
        line_bot_api.push_message(
            user,
            TextSendMessage(base_text + str(time) + "です。")
        )
    print("Completed: warn_lazy_user.py")
