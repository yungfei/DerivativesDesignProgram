"""
尝试用backtrader回测交叉对冲策略

切记，backtradwer的核心在__init__ 和next中

"""


from __future__ import (absolute_import, division, print_function,unicode_literals)
import backtrader as bt
import akshare as ak
import pandas as pd
from datetime import datetime
import numpy as np


class percent(bt.Sizer):
    params = (
        ('percents', 10),
        ('retint', False),  # 返回整数
    )

    def __init__(self):
        pass

    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.broker.getposition(data)
        if not position:
            size = cash / data.close[0] * (self.params.percents / 100)
        else:
            size = position.size

        if self.p.retint:
            size = int(size)

        return size

class PandasData_more(bt.feeds.PandasData):
    lines = ('return_rate', ) # 要添加的线
    # 设置 line 在数据源上的列位置
    params=(
        ('return_rate', -1),
           )
    # -1表示自动按列明匹配数据，也可以设置为线在数据源中列的位置索引 (('pe',6),('pb',7),)


class SmaStrategy(bt.Strategy):
    # 可配置策略参数
    params = dict(
        SMA1_period = 5,    # 小均线周期
        SMA2_period = 10,   # 大均线周期
        stake = 100,            # 单笔交易股票数目
        beta_period = 10, # 用于计算beta的期限长短
        printlog = False,
    )

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function fot this strategy'''
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def stop(self):
        self.log('Ending Value %.2f' %
                 (self.broker.getvalue()), doprint=True)

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

    def __init__(self):
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
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        pos = self.getposition(self.datas[0])
        if not len(pos):
            if self.SMA1 > self.SMA2:             # 达到买入条件
                index_sub = self.datas[0].return_rate.get(ago=-1, size = self.params.beta_period)


                if len(index_sub):
                    self.cal_beta(index_sub) # 更新beta值
                    self.future_stake = self.beta * self.datas[0].close.get()[0]* self.params.stake / self.datas[1].close.get()[0]

                    # 买入指数的同时做空期货
                    self.buy(data=self.datas[0], size=self.params.stake)
                    self.sell(data=self.datas[1], size=self.future_stake)

                    print("已买入股指并进行对冲")

        elif self.SMA1 < self.SMA2:               # 达到卖出条件
            # 买入指数的同时做空期货
            self.sell(data=self.datas[0], size=self.params.stake)
            self.buy(data=self.datas[1], size=self.future_stake)
            print("已平仓")


# 获取A股HS300股指
index_data = ak.stock_zh_index_daily("sh000300")
index_data.index = pd.to_datetime(index_data.index)
index_data["date"] = index_data.index
index_data["return_rate"] = index_data.close.diff(1)/index_data.close.shift(1)



future_data = ak.futures_zh_daily_sina("IF0").iloc[:,:6]
future_data.index = pd.to_datetime(future_data["date"])
future_data["return_rate"] = future_data.close.diff(1)/future_data.close.shift(1)



# 将pandas数据DF导入到实例化对象中
start_date = datetime(2021, 7, 3)  # 回测开始时间
end_date = datetime(2021, 8, 30)  # 回测结束时间
data_index = PandasData_more(dataname=index_data, fromdate=start_date, todate=end_date)  # 加载数据
data_future = PandasData_more(dataname=future_data, fromdate=start_date, todate=end_date)  # 加载数据

# 实例化对象
cerebro = bt.Cerebro()

cerebro.adddata(data_index, name="index")
cerebro.adddata(data_future, name="future")



# 设置启动资金
startcash = 1000000000.0
cerebro.broker.setcash(startcash)
# 设置交易手续费为 0.05%
# cerebro.broker.setcommission(commission=0.0005)
# 设置订单份额
cerebro.addsizer(percent)
# 将交易策略加载到回测系统中
cerebro.addstrategy(SmaStrategy)


import backtrader.analyzers as btay#添加分析函数
# 添加分析对象
cerebro.addanalyzer(btay.SharpeRatio,_name="sharpe")
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DW')


# 运行回测
results = cerebro.run()
# 打印最后结果

portvalue = cerebro.broker.getvalue()
pnl = portvalue - startcash


#打印结果
print(f'总资金: {round(portvalue,2)}')
print(f'净收益: {round(pnl,2)}')
print("夏普比例:", results[0].analyzers.sharpe.get_analysis())
print("回撤",results[0].analyzers.DW.get_analysis())

#%%

cerebro.plot(style = "candlestick")  # 绘图


