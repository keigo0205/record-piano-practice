from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

line_bot_api = LineBotApi('<channel access token>')

try:
    line_bot_api.reply_message('<reply_token>', TextSendMessage(text='Hello World!'))
except LineBotApiError as e:
    # error handle
    pass
