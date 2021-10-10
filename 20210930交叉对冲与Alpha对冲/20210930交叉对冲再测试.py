"""
用HS300股指期货对冲浦发股票
数据来源：Akshare
回测框架：backtrader
"""

from __future__ import (absolute_import, division, print_function,unicode_literals)
import backtrader as bt
import akshare as ak
import pandas as pd
from datetime import datetime
import numpy as np

class PandasData_more(bt.feeds.PandasData):
    lines = ('return_rate', ) # 要添加的线
    # 设置 line 在数据源上的列位置
    params=(
        ('return_rate', -1),
           )
    # -1表示自动按列明匹配数据，也可以设置为线在数据源中列的位置索引 (('pe',6),('pb',7),)

def AddData(cerebro, start_date, end_date, matrix_name):
    future_data = pd.read_csv("data/%s.csv" % matrix_name, index_col="Unnamed: 0")
    future_data.index = pd.to_datetime(future_data["date"])

    data_future = PandasData_more(dataname=future_data, fromdate=start_date, todate=end_date)  # 加载数据
    cerebro.adddata(data_future, name=matrix_name)
    print("数据%s填充完毕！" % matrix_name)

    return None

class Strategy(bt.Strategy):
    # 不变参数
    params = dict(
        SMA1_period=5,  # 小均线周期
        SMA2_period=10,  # 大均线周期
        stake=100000,  # 单笔交易股票数目
        beta_period=10,  # 用于计算beta的期限长短
        printlog=False,
    )

    def __init__(self):
        # 可变参数-核心1
        # 计算大小周期移动平均值，以设置买卖点
        self.SMA1 = bt.ind.SMA(self.datas[0].close, period=self.params.SMA1_period)
        self.SMA2 = bt.ind.SMA(self.datas[0].close, period=self.params.SMA2_period)

        # 其他变量
        self.beta = 0
        self.future_stake = 0

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def next(self):
        # 核心2：策略设置

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        pos = self.getposition(self.datas[0])
        if not len(pos):
            if self.SMA1 > self.SMA2:  # 达到买入条件
                index_sub = self.datas[0].return_rate.get(ago=-1, size=self.params.beta_period)

                if len(index_sub):
                    print("更新beta")
                    self.cal_beta(index_sub)  # 更新beta值
                    self.future_stake = self.beta * self.datas[0].close.get()[0] * self.params.stake / \
                                        self.datas[1].close.get()[0]

                    # 买入指数的同时做空期货
                    self.order = self.buy(data=self.datas[0], size=self.params.stake)
                    # self.order = self.sell(data=self.datas[1], size=self.future_stake)

                    self.log("已执行空头对冲策略")

        elif self.SMA1 < self.SMA2:  # 达到卖出条件
            # 买入指数的同时做空期货
            self.order = self.sell(data=self.datas[0], size=self.params.stake)
            # self.order = self.buy(data=self.datas[1], size=self.future_stake)
            self.log("已执行平仓操作")

    def log(self, txt, dt=None):
        ''' 打印信息系统'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        """买卖操作执行的打印"""
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        """打印净利润"""
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def cal_beta(self, SeriesA):
        """
        计算两列数据的Beta值
        :param SeriesA: 被对冲标的收益率列
        :param SeriesB: 对冲标的收益率列
        :return: Beta值
        """
        SeriesB = self.datas[1].return_rate.get(ago=-1, size=self.params.beta_period)

        cov_sm = np.cov(SeriesB,SeriesA)[0,1]
        var_m = np.var(SeriesB)

        self.beta = cov_sm / var_m

        return None


# step0: 获取数据并保存在本地
# 获取期货数据
"""
future_data = ak.futures_zh_daily_sina("IF0").iloc[:,:6]
future_data["return_rate"] = future_data.close.diff(1)/future_data.close.shift(1)
future_data.to_csv("data/future_data.csv")
"""

# 获取浦发股票
"""
stock_data = ak.stock_zh_a_hist(symbol="600000", period="daily").iloc[:,:6]
stock_data.columns = future_data.columns[:6]
stock_data["return_rate"] = stock_data.close.diff(1)/stock_data.close.shift(1)
stock_data.to_csv("data/stock_data.csv")

stock_data = pd.read_csv("data/stock_data.csv", index_col="Unnamed: 0")
stock_data.index = pd.to_datetime(stock_data["date"])
"""

# 准备回测开始结束日期
start_date = datetime(2020, 7, 3)  # 回测开始时间
end_date = datetime(2021, 8, 30)  # 回测结束时间

# 数据填充（记得第二个填充期货）
cerebro = bt.Cerebro()
AddData(cerebro= cerebro, matrix_name="stock_data", start_date=start_date, end_date=end_date)
AddData(cerebro= cerebro, matrix_name="future_data", start_date=start_date, end_date=end_date)

# 策略设计
# 策略设计完成

# 模型初始化参数
cerebro.broker.setcash(cash=100000000)
cerebro.broker.setcommission(commission=0.00025)

# 将交易策略加载到回测系统中
cerebro.addstrategy(Strategy)


import backtrader.analyzers as btay#添加分析函数
# 添加分析对象
cerebro.addanalyzer(btay.SharpeRatio,_name="sharpe")
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DW')


# 运行回测
results = cerebro.run()
# 打印最后结果

portvalue = cerebro.broker.getvalue()
pnl = portvalue - 100000000


#打印结果
print(f'总资金: {round(portvalue,2)}')
print(f'净收益: {round(pnl,2)}')
print("夏普比例:", results[0].analyzers.sharpe.get_analysis())
print("回撤",results[0].analyzers.DW.get_analysis())

#%%

cerebro.plot(style = "candlestick")  # 绘图
