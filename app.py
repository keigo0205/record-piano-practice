# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from __future__ import unicode_literals

import os
import sys
import psycopg2
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookParser, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)


app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)
handler = WebhookHandler(channel_secret)

DATABASE_URL = os.environ['DATABASE_URL']
DB_NAME = "test_table"


def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')


def countPracticeData(user_id, text):
    sql = "SELECT count(user_id = '" + user_id + "' and message = '" + text + "' or NULL ) from " + DB_NAME
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            results = cur.fetchall()
    return results[0][0]


def insertPracticeData(user_id, text):
    sql = "INSERT INTO " + DB_NAME + " VALUES ('" + user_id + "','" + text + "',current_timestamp)"
    with get_connection() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql)
    return


def updatePracticeData(user_id, text):
    sql = """
    UPDATE %s SET last_practice_date = current_timestamp
    WHERE user_id = '%s' and message = '%s'
    """ % (DB_NAME, user_id, text)
    with get_connection() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql)
    return


def getListMessage(user_id, text):
    sql = 'select * from ' + DB_NAME + ' where user_id = %(target_id)s'
    with get_connection() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql, {'target_id': (user_id,)})
            results = cur.fetchall()

    if len(results) == 0:
        return "登録がありません。"

    ret = ''
    for result in results:
        _, piece, time = result
        ret += piece + " を最後に練習したのは\n"
        ret += str(time) + " です。\n\n"

    return ret


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
        else:
            handler.handle(body, signature)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text
    if event.message.text in ["リスト", "list"]:
        list_message = getListMessage(user_id, text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=list_message)
        )
        return 'OK'

    user_id = event.source.user_id
    text = event.message.text
    is_data = countPracticeData(user_id, text) > 0
    if is_data is True:
        updatePracticeData(user_id, text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="時刻を更新しました。")
        )
    else:
        insertPracticeData(user_id, text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="登録しました。")
        )
    return 'OK'


if __name__ == "__main__":
    DATABASE_URL = os.environ['DATABASE_URL']
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')

    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=int(os.environ.get('PORT', 8000)), help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    arg_parser.add_argument('--host', default='0.0.0.0', help='host')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, host=options.host, port=options.port)
