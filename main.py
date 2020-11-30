from flask import Flask, request, abort
from humidity.humidity import humidity_calc
import os

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

@app.route("/")
def hello_world():
    return "hello world!"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        receive_message =  event.message.text
        city_name, temperature, humidity_rate = receive_message.split("\n")

        # 文字列の置換
        for rep in ["度", "℃", "ど"]:
            temperature = temperature.replace(rep, "")
        for rep in ["％", "%", "ぱーせんと", "パーセント", "percent"]:
            humidity_rate = humidity_rate.replace(rep, "")

        predict_humidity = humidity_calc(city_name, int(temperature), float(humidity_rate))
        if predict_humidity >= 100:
            send_message = """
            結露ができそうだよ
            """
        else:
            send_message = """
            湿度は{0}%になりそうだよ
            """.format(predict_humidity)

    except:
        send_message = """
        市町村名
        温度
        湿度
        で送信してください。
        
        ---例---
        新宿区
        25℃
        70％
        """
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=send_message))

if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)