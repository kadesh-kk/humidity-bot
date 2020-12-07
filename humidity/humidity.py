import json
import os
import psycopg2
import datetime
import pickle


# city_dict = {
#     "八王子市":"東京地方",
#     "町田市":"東京地方",
#     "新宿区":"東京地方",
#     "町田市":"東京地方"
# }

# class ForecastData():
#     def __init__(self, name, min_temperature, max_temperature):
#         self.name = name
#         self.min_temperature = min_temperature
#         self.max_temperature = max_temperature
#
#     def view(self):
#         print("地方：{0}\n最高気温：{1:2d}℃\n最低気温：{2:2d}℃\n".format(self.name, self.max_temperature, self.min_temperature))

# PostgreSQLとの接続を行う
def get_connection():
    dsn = os.environ.get('DATABASE_URL')
    return psycopg2.connect(dsn)

def from_database(pref_name, country_name):
    # 1日後のデータを取得
    dt_now = datetime.datetime.now()
    # 20時にスクレイピングを行うため(時差9時間を考慮)
    if dt_now.hour >= 11:
        dt_now = dt_now + datetime.timedelta(days=1)

    query = """
        SELECT min_temperature
        FROM forecast_tb
        WHERE prefname = '{0}'
        AND country_name = '{1}'
        AND year = {2}
        AND month = {3}
        AND date = {4}
        """.format(pref_name, country_name, dt_now.year, dt_now.month, dt_now.day)

    with get_connection() as conn:
        # クエリを編集する
        with conn.cursor() as cur:
            cur.execute(query)
            (min_temperature,) = cur.fetchone()

    return min_temperature

# 飽和水蒸気量を計算する関数
def max_humidity_calc(temperature):
    # eは飽和水蒸気圧, aは飽和水蒸気圧
    e = 6.11 * 10 ** (7.5 * temperature / (237.3 + temperature))
    a = 217 * e / (temperature + 273.15)
    return round(a, 2) # 小数点2桁まで表示

def humidity_calc(pref_name, city_name, temperature, humidity_rate):
    # # JSONデータの読み込み
    # with open("./humidity/pkl/forecast_data.json") as f:
    #     forecast_data_dict = json.load(f)

    # pickleから自治体の区分を取り出す
    with open("./humidity/pkl/country.pickle", mode='rb') as f:
        pref_city_dict = pickle.load(f)

    country_name = pref_city_dict[pref_name][city_name]

    # min_temperature = forecast_data_dict[pref_name][city_name]["min_temperature"]

    min_temperature = from_database(pref_name, country_name)

    # 現在の水蒸気量の計算
    now__humidity = max_humidity_calc(temperature) * humidity_rate

    # 飽和水蒸気量の計算
    max_humidity = max_humidity_calc(min_temperature)

    return round(now__humidity / max_humidity, 1) # 最低気温の湿度計算



