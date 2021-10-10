"""
进行欧洲美元利率曲率调整（凸性调整）和计算远期利率
"""

import pandas as pd
import numpy as np

EDData = pd.read_csv("data/20211010EURODPLLAR.csv")
EDData = EDData.replace("-" , np.nan).dropna()

# 曲率调整
# sigma = np.std([100 - float(x) for x in EDData[EDData["PERIODT1"] <= 1]["LAST"]])
sigma = 0.012 # sigma的计算方式有待继续学习
EDData["ConveAdjust"] = 0.5 * sigma * sigma * EDData["PERIODT1"] * EDData["PERIODT2"]
EDData["FutureRate"] = [100 - float(x) for x in EDData["LAST"]]

EDData["ForwardRate"] = np.log(EDData["FutureRate"]/400+1)* 365/90 - EDData["ConveAdjust"]
EDData.to_csv("data/20211010ConveAdjust.csv", index=False)
EDData.to_excel("data/20211010ConveAdjust.xlsx", index = False)

# libor利率
import akshare as ak

rate_interbank_df = ak.rate_interbank(market="伦敦银行同业拆借市场", symbol="Libor美元", indicator="12月", need_page="15")
