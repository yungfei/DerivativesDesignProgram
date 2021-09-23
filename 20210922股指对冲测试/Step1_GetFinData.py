"""
本步骤用于获取实行策略所用的数据
"""


import akshare as ak
import pandas as pd
import numpy as np


# 获取股指数据及股指期货数据, 以hs300主力期货（IF9999.CCFX）和HS300指数对冲
HS_futures = ak.futures_zh_daily_sina("IF0")
PF_stock =  ak.stock_zh_a_hist(symbol="600000", period="daily", start_date="20170101", end_date='20220907', adjust="")
HS_index = ak.stock_zh_index_daily("sh000300")
HS_index["date"] = [str(x)[:10] for x in HS_index.index]
# HS_futures.to_csv("data/HS_futures.csv", index=False)
# HS_index.to_csv("data/HS_index.csv", index=False)

# 处理数据：均以收盘价作为结算价格,并按照期货交易日期合并期货和股指的收盘价(期货存在时间短）
list = []
for i in range(len(HS_futures)):
    dates = HS_futures.iloc[i,0]
    ft_close = HS_futures.iloc[i,4]
    try:
        hs_close = HS_index[HS_index["date"] == dates].close[0]
        PF_close = PF_stock[PF_stock["日期"] == dates].iloc[0,2]
    except:
        hs_close = np.nan
    list.append([dates, ft_close, hs_close, PF_close])

fu_idx_close  = pd.DataFrame(list, columns=["date", "future", "index", "PF"])
fu_idx_close.to_csv("data/fu_idx_PF_close.csv", index= False)
