import requests
from bs4 import BeautifulSoup

city_dict = {
    "八王子市":"東京地方",
    "町田市":"東京地方",
    "新宿区":"東京地方",
    "町田市":"東京地方"
}

class ForecastData():
    def __init__(self, name, min_temperature, max_temperature):
        self.name = name
        self.min_temperature = min_temperature
        self.max_temperature = max_temperature

    def view(self):
        print("地方：{0}\n最高気温：{1:2d}℃\n最低気温：{2:2d}℃\n".format(self.name, self.max_temperature, self.min_temperature))


# 飽和水蒸気量を計算する関数
def max_humidity_calc(temperature):
    # eは飽和水蒸気圧, aは飽和水蒸気圧
    e = 6.11 * 10 ** (7.5 * temperature / (237.3 + temperature))
    a = 217 * e / (temperature + 273.15)
    return round(a, 2) # 小数点2桁まで表示

def humidity_calc(city_name, temperature, humidity_rate):
    # スクレイピングの処理
    base_url = "https://www.jma.go.jp/jp/yoho/319.html"
    r = requests.get(base_url)
    r.encoding = r.apparent_encoding

    soup = BeautifulSoup(r.text)

    name_list = soup.find_all("div", style="float: left")
    min_temp_list = soup.find_all("td", class_="min")
    max_temp_list = soup.find_all("td", class_="max")

    # 最低気温、最高気温は奇数の時のみ処理をする
    min_temp_list = [m for i, m in enumerate(min_temp_list) if i % 2 == 1]
    max_temp_list = [m for i, m in enumerate(max_temp_list) if i % 2 == 1]

    #
    data_dict = {}
    for name, min_temp, max_temp in zip(name_list, min_temp_list, max_temp_list):
        name = name.string
        min_temp = min_temp.string.replace("度", "")
        max_temp = max_temp.string.replace("度", "")

        data = ForecastData(name, int(min_temp), int(max_temp))
        # data.view()

        data_dict[name] = data

    city_class = city_dict[city_name]
    fc = data_dict[city_class] # ForecastData のデータ

    # 現在の水蒸気量の計算
    now__humidity = max_humidity_calc(temperature) * humidity_rate
    # 飽和水蒸気量の計算
    max_humidity = max_humidity_calc(fc.min_temperature)

    return round(now__humidity / max_humidity, 1) # 最低気温の湿度計算



