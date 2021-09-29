"""
虽然名字叫概念学习，但半道就走偏了，想着怎么去把股票组合用起来做回测
有个奇怪的想法，其实股票也好，期货也好，说实话从数据格式上来说是很相似的
那么做策略的时候能不能把期货当股票一样处理呢？
不懂，学吧

20210928:
我大概搞清楚一点要怎么搞多组数据了，其实也挺好玩
对于数组的理解是很基于想象的，文字写出来还挺难
如果你有疑问的话，欢迎一起讨论交流。Q：1774590035
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import backtrader as bt
import akshare as ak
import pandas as pd
from datetime import datetime


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


class SmaStrategy(bt.Strategy):
    # 可配置策略参数
    params = dict(
        period = 10,    # 均线周期
        stake = 100,            # 单笔交易股票数目
    )

    def __init__(self):
        self.inds = dict()
        for i, d in enumerate(self.datas):
            self.inds[d] = bt.ind.SMA(d.close, period=self.p.period)

    def next(self):
        for i, d in enumerate(self.datas):
            pos = self.getposition(d)
            if not len(pos):
                if d.close[0] > self.inds[d][0]:             # 达到买入条件
                    self.sell(data = d, size = self.p.stake)

            elif d.close[0] < self.inds[d][0]:               # 达到卖出条件
                self.buy(data = d)
                print(len(pos))



def get_data(symbol, start_date="20210101", end_date='20210907'):
    data = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date,adjust="").iloc[:, :6]
    data.columns = [
        'date',
        'open',
        'close',
        'high',
        'low',
        'volume',
    ]
    data.index = pd.to_datetime(data['date'])

    return data



if __name__ == "__main__":
    cerebro = bt.Cerebro()  # 初始化cerebro

    # 将多只股票数据加载进模型
    stock_list = ["000537", "603992", "300610"]

    for symbol in stock_list:
        df = get_data(symbol)

        # 将pandas数据DF导入到实例化对象中
        start_date = datetime(2021, 7, 3)  # 回测开始时间
        end_date = datetime(2021, 8, 30)  # 回测结束时间
        data = bt.feeds.PandasData(dataname=df, fromdate=start_date, todate=end_date)  # 加载数据
        cerebro.adddata(data, name=symbol)

    # 设置启动资金
    startcash = 10000000.0
    cerebro.broker.setcash(startcash)
    # 设置交易手续费为 0.05%
    cerebro.broker.setcommission(commission=0.0005)
    # 设置订单份额
    cerebro.addsizer(percent)
    # 将交易策略加载到回测系统中
    cerebro.addstrategy(SmaStrategy)

    results = cerebro.run()