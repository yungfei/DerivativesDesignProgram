"""
本步骤将尝试利用期货指数对冲股指或者浦发股票的波动
回测期限设置为最近100个交易日， beta计算期限设定为回测期限前200个交易日数据，回测设置持有期限为5日
可调整回测期限、beta计算期限、回测持有期限

模型假设和设计：
浦发股指的点位在10点左右，假设买入20万支股票（2000手），即大概风险敞口在200万元整
模型假设股指期货可取非整数份数（实际上每张股指期货是点数*300计算价格）
假设每次股票持有期限为5天（即第一天前一天收盘价买入，第5个交易日收盘价卖出），同步进行股指空头对冲
对冲期间不考虑整个期货的保证金运行状况，按照中金所IF0品种介绍，该股指期货最低保证金比例为10%,即以10%计算初始资金成本

"""

import pandas as pd
import numpy as np


def cal_Beta(data):
    """
    用于计算两组数的beta值
    :param data: data的输入格式必须与上述文件中导入的data格式相符
    :return:
    """
    returns = []
    for i in range(len(data) - 1):
        A_return = data.iloc[i + 1, 2] / data.iloc[i, 2] - 1
        B_return = data.iloc[i + 1, 0] / data.iloc[i, 0] - 1
        returns.append([A_return, B_return])
    returns_df = pd.DataFrame(returns, columns=["A", "B"]) * 100

    var = np.var(returns_df["B"])
    covar = np.cov(returns_df["A"], returns_df["B"])[0, 1]

    beta = covar / var

    return beta


def future_hedge_design(back_test_date, cal_beta_date, sto_call_number, hold_period, Margin_ratio):
    """
    对冲策略回测设计
    :param back_test_date: 回测期限
    :param cal_beta_date: 贝塔计算期限
    :param sto_call_number: 股票买入数量
    :param hold_period: 持有期限
    :param Margin_ratio: 保证金比例
    """
    # 导入数据
    data = pd.read_csv("data/fu_idx_PF_close.csv", index_col="date")

    cal_beta_period = data.iloc[-(cal_beta_date + back_test_date):-back_test_date, :]
    backtest_period = data.iloc[-back_test_date - 1:, :]
    # 根据贝塔计算对冲策略和收益

    beta = cal_Beta(cal_beta_period)  # 计算beta值
    cycle = int(len(backtest_period) / hold_period)

    list = []
    for i in range(cycle):
        # 确定股票价格、股指期货价格、合约数量
        stoP0 = backtest_period.iloc[i, 2]  # 浦发初始价格
        futP0 = backtest_period.iloc[i, 0]  # 沪深300期初价格
        N = beta * (stoP0 * sto_call_number) / (futP0 * 300)  # 对冲合约数量

        # 计算持有到期日净收益
        stoP1 = backtest_period.iloc[i + 5, 2]  # 浦发到期价格
        futP1 = backtest_period.iloc[i + 5, 0]  # 沪深300期末价格

        return_ = (stoP1 - stoP0) * sto_call_number + N * (futP0 - futP1) * 300  # 对冲总体收益（按元计算）
        PF_retrun = (stoP1 - stoP0) * sto_call_number
        Future_return =  N * (futP0 - futP1) * 300

        list.append([return_,PF_retrun, Future_return])

    df = pd.DataFrame(list, columns=["Hedge_return", "PF_retrun", "Future_return"])

    # 计算平均收益率，收益，资金成本，beta， 回测期限，beta计算期限
    average_data = [x for x in np.mean(df)]
    output_sub = [back_test_date, cal_beta_date, sto_call_number, hold_period, Margin_ratio, beta] + average_data

    return output_sub

#*******************************************************************************

# 预设值设置
back_test_date = 100 # 回测期限
cal_beta_date = 200 # 贝塔计算期限
sto_call_number = 200000  # 股票买入数量
hold_period = 5  # 持有期限
Margin_ratio = 0.1  # 保证金比例


output = []
for i in range(50, 110, 10):
    for j in range(10,210, 10):
        for k in range(5,25, 5):
            back_test_date = i  # 回测期限
            cal_beta_date = j  # 贝塔计算期限
            sto_call_number = 200000  # 股票买入数量
            hold_period = k  # 持有期限
            Margin_ratio = 0.1  # 保证金比例

            output_sub = future_hedge_design(back_test_date, cal_beta_date, sto_call_number, hold_period, Margin_ratio)
            output.append(output_sub)

output_df = pd.DataFrame(output, columns=["back_test_date", "cal_beta_date", "sto_call_number", "hold_period", "Margin_ratio", "beta", "Hedge_return", "PF_retrun", "Future_return"])

output_df.to_csv("data/HedgeDesign1.csv", index=False)
output_df.to_excel("data/HedgeDesign1.xlsx", index=False)
















