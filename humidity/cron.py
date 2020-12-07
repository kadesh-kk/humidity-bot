import requests
from bs4 import BeautifulSoup
import csv
import pickle
import json
import time
import datetime
import psycopg2
import os

# pickle 関連の処理
def pickle_dump(pkl_obj, path):
    with open(path, mode='wb') as f:
        pickle.dump(pkl_obj, f)

def pickle_load(path):
    with open(path, mode='rb') as f:
        pickle_data = pickle.load(f)
        return pickle_data

# 気温データのクラス
class ForecastData():
    def __init__(self, year, month, day, pref_name, country_name, min_temperature, max_temperature):
        self.year = year
        self.month = month
        self.day = day
        self.pref_name = pref_name
        self.country_name = country_name
        self.min_temperature = min_temperature
        self.max_temperature = max_temperature

    def view(self):
        print("日時：{0:4d}年{1:2d}月{2:2d}日\n地方：{3}\n最高気温：{4:2d}℃\n最低気温：{5:2d}℃\n".format(self.year,
                                                                                      self.month,self.day,
                                                                                      self.country_name,
                                                                                      self.max_temperature,
                                                                                      self.min_temperature))

    def data_to_list(self):
        fc_data_dict = vars(self)
        fc_data_list = [v for k, v in fc_data_dict.items()]
        return fc_data_list

# スクレイピングの処理
def scraping(base_url):
    time.sleep(1)
    res = requests.get(base_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    return soup

# データ作成の処理
def forecast_extract(soup, pref_name):
    # 引数：  beautifulsoupのsoup, 県名
    # 戻り値：リスト

    # 現在時刻の算出
    dt_now = datetime.datetime.now() + datetime.timedelta(days=1)
    year = dt_now.year
    month = dt_now.month
    day = dt_now.day

    # soupの処理
    country_name_list = soup.find_all("div", style="float: left")
    min_temp_list = soup.find_all("td", class_="min")
    max_temp_list = soup.find_all("td", class_="max")

    # 最低気温、最高気温は奇数の時のみ処理をする
    # 2つ以上存在する場合の処理を考える
    min_temp_list = [m for i, m in enumerate(min_temp_list) if i % 2 == 1]
    max_temp_list = [m for i, m in enumerate(max_temp_list) if i % 2 == 1]

    f_data_list = []
    for country_name, min_temp, max_temp in zip(country_name_list, min_temp_list, max_temp_list):
        country_name = country_name.string
        min_temp = min_temp.string.replace("度", "")
        max_temp = max_temp.string.replace("度", "")

        f_data = ForecastData(year, month, day, pref_name, country_name, int(min_temp), int(max_temp))
        #         data.view()

        f_data_list.append(f_data.data_to_list())
        # f_data_dict[country_name] = vars(f_data)

    return f_data_list

def get_connection():
    dsn = os.environ.get('DATABASE_URL')
    return psycopg2.connect(dsn)

def to_database(forecast_data_list):
    # 引数: data_list は2重の配列

    # 1次元配列の結合
    def list_join(d_l):
        s = ""
        for i, d in enumerate(d_l):
            if type(d) == str:
                s += "'{0}'".format(d)
            else:
                s += str(d)
            # 最後の文字の場合、", "はつけない
            if i != len(d_l) - 1:
                s += ", "

        return s

    # PostgreSQLとの接続
    query_data = ""
    for i, d_l in enumerate(forecast_data_list):
        one_data = list_join(d_l)

        # 最後のみ, をつけない
        if i == len(forecast_data_list) - 1:
            query_data += "({0})".format(one_data)
        else:
            query_data += "({0}), ".format(one_data)

    # 最後の1文字目
    query = """
    INSERT INTO forecast_tb (
        id, 
        year, 
        month, 
        date, 
        pref_name, 
        country_name, 
        min_temperature, 
        max_temperature) VALUES {0};""".format(query_data)

    with get_connection() as conn:
        # クエリを編集する
        with conn.cursor() as cur:
            cur.execute(query)
        conn.commit()  # コミット

def cron_main():
    # URLを取り出す
    url_dict = pickle_load("./humidity/pkl/forecast_url.pickle")

    # スクレイピングの処理
    forecast_data_list = []
    for pref_name, url in url_dict.items():
        soup = scraping(url)
        data_list = forecast_extract(soup, pref_name)

        forecast_data_list += data_list
    # print(forecast_data_list)

    # この下にDBの処理を行う
    to_database(forecast_data_list)

    # JSONデータで保存する
    # with open("./humidity/pkl/forecast_data.json", "w") as f:
    #     json.dump(forecast_data_dict, f, indent=4)

# スクレイピングを実行
if __name__ == '__main__':
    cron_main()
