"""
该脚本用于下载芝商所当天的欧洲美元数据
"""

import pandas as pd
from selenium import webdriver
import calendar


url = "https://www.cmegroup.com/markets/interest-rates/stirs/eurodollar.quotes.html"

driver = webdriver.Chrome()
driver.get(url)

try:
    driver.find_element_by_xpath('//div/button[@class=" primary load-all btn btn-"]').click()
except:
    pass


# scrapy data[4-10]
month_xpath = '//tbody/tr/td/div[@class="table-cell month-code"]/span/b'
month_text = [x.text for x in driver.find_elements_by_xpath(month_xpath)]



list_ = [month_text]
for series_id in range(4,11):
    series_xpath = '//tbody/tr/td[%d]/div[@class="table-cell"]' % series_id
    series_text = [x.text for x in driver.find_elements_by_xpath(series_xpath)]

    list_.append(series_text)


col_names = ["MONTH","LAST", "CHANGE", "PRIOR SETTLE","OPEN","HIGH", "LOW", "VOLUME"]
df = pd.DataFrame(list_).T
df.columns = col_names

def CAL_CHANGE(LAST, PRIOR):
    try:
        return float(LAST)-float(PRIOR)
    except:
        return "-"


df["CHANGE"] = df.apply(lambda x: CAL_CHANGE(x["LAST"], x["PRIOR SETTLE"]) , axis=1)
df["VOLUME"] = df["VOLUME"].apply(lambda x: x.replace(",",""))

driver.close()

def transfer_date(date_string):
    mon, year = date_string.split(" ")
    date = year + str(list(calendar.month_abbr).index(mon[0] + mon[1:].lower())).zfill(2)
    return date

df["MONTH"] = df["MONTH"].apply(lambda x: transfer_date(x))
df["MONTH"] = df["MONTH"].apply(lambda x: x+"01")
df["year"] = df["MONTH"].apply(lambda x: int(x[:4]))
df["month"] = df["MONTH"].apply(lambda x: int(x[4:6]))
df["PERIODT1"] = df["year"]-2021 + (df["month"] - 10)/ 12 # 距今多少期限
df["PERIODT2"] = df["PERIODT1"] + 0.25 # 欧洲美元期货到期距今期限，方便计算曲率调整


# get times and output data
import datetime
times = datetime.datetime.now().strftime("%Y%m%d")
df.to_csv("data/%sEURODPLLAR.csv" % times, index=False)
df.to_excel("data/%sEURODPLLAR.xlsx" % times, index=False)


# use akshare API obtain LIBOR USD data
import akshare as ak

period = ["隔夜", "1周", "1月", "2月" ,"3月", "8月"]

libro_list = []
for i in period:
    rate_interbank_df = ak.rate_interbank(market="伦敦银行同业拆借市场", symbol="Libor美元", indicator=i, need_page="15")
    rate_interbank_df["品类"] = i

    libro_list.append(rate_interbank_df)

libor_df = pd.concat(libro_list, axis=0)
libor_df.to_csv("data/LiborData.csv", index = False)
libor_df.to_excel("data/LiborData.xlsx", index = False)