from flask import Flask, request, abort, render_template
from humidity.humidity import humidity_calc
import datetime
import os
# import pickle

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__, static_folder='static', template_folder='templates')

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

@app.route("/index", methods = ["GET", "POST"])
def top_page():
    if request.method == "GET":
        return render_template("index.html")
    else:
        # 湿度の計算
        pref_name = request.form["prefectures"]
        city_name = request.form["city"]
        temperature = 13
        humidity_rate = 25
        predict_humidity = humidity_calc(pref_name, city_name, int(temperature), float(humidity_rate))

        # 湿度が100%以上となっている場合
        if predict_humidity > 100:
            predict_humidity = 100

        return render_template("humidity.html",
                               pref_name = pref_name,
                               city_name = city_name,
                               predict_humidity =predict_humidity)

# @app.route("/")
# def hello_world():
#     dt_now = datetime.datetime.now()
#     dt_next_day = datetime.datetime.now()
#     morning_str = "今朝"
#     if dt_now.hour >= 11 and dt_now.hour < 14:
#         morning_str = "明日の朝"
#
#     # 20時にスクレイピングを行うため、20時以前は前日のデータを参照する。
#     if dt_now.hour > 10:
#         dt_next_day = dt_now + datetime.timedelta(days = 1)
#
#     pref_name = "東京都"
#     city_name = "八王子市"
#     temperature = 13
#     humidity_rate = 25
#     predict_humidity = humidity_calc(pref_name, city_name, int(temperature), float(humidity_rate))
#
#     return "hello world!<br>今は{0}年{1}月{2}日 {3}時です!<br>{4}の東京都八王子市の湿度は{5}%だよ!".format(dt_now.year, dt_now.month, dt_now.day, dt_now.hour, morning_str, predict_humidity)

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
        pref_name, city_name, temperature, humidity_rate = receive_message.split("\n")

        # 文字列の置換
        for rep in ["度", "℃", "ど"]:
            temperature = temperature.replace(rep, "")
        for rep in ["％", "%", "ぱーせんと", "パーセント", "percent"]:
            humidity_rate = humidity_rate.replace(rep, "")

        predict_humidity = humidity_calc(pref_name, city_name, int(temperature), float(humidity_rate))
        if predict_humidity >= 100:
            send_message = "結露ができそうだよ"
        else:
            send_message = "湿度は{0}%になりそうだよ".format(predict_humidity)

    except:
        send_message = "都道府県名\n市町村名\n温度\n湿度\nで送信してください。\n\n---例---\n東京都\n新宿区\n25℃\n70％\n"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=send_message))

if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)