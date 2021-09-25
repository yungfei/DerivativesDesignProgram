"""
本脚本用于对于步骤二中代码的矩阵化计算，加快计算速度并尝试改进算法
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def cal_Beta(data):
    """
    用于计算两组数的beta值
    :param data: data的输入格式必须与上述文件中导入的data格式相符
    :return:
    """
    data = np.array(data)
    return_matrix = (data[1:,:] / data[:-1,:] - 1) * 100 # 计算收益率矩阵
    beta = np.cov(return_matrix[:,0], return_matrix[:,2])[0, 1] / np.var(return_matrix[:,0])

    return beta

def cal_retruns(backtest_period, beta,sto_call_number = 200000):
    """
    确定三项收益：对冲收益、股票收益、期货收益
    :param backtest_period:
    :param beta:
    :return:
    """
    # 确定股票价格、股指期货价格、合约数量
    stoP0 = backtest_period[0, 2]  # 浦发初始价格
    futP0 = backtest_period[0, 0]  # 沪深300期初价格
    N = beta * (stoP0 * sto_call_number) / (futP0 * 300)  # 对冲合约数量

    # 计算持有到期日净收益
    stoP1 = backtest_period[-1, 2]  # 浦发到期价格
    futP1 = backtest_period[-1, 0]  # 沪深300期末价格

    return_ = (stoP1 - stoP0) * sto_call_number + N * (futP0 - futP1) * 300  # 对冲总体收益（按元计算）
    PF_retrun = (stoP1 - stoP0) * sto_call_number
    Future_return = N * (futP0 - futP1) * 300

    return return_,PF_retrun,Future_return

def future_hedge_design(data, back_test_date = 30, cal_beta_date = 5 ,hold_period = 5 ):
    """
    对冲策略回测设计
    :param data:输入的原始数据
    :param back_test_date: 回测开始期限（为倒数第多少个交易日）
    :param cal_beta_date: 贝塔计算期限（拟改造为新的变量）
    :param sto_call_number股票买入数量
    :param hold_period: 持有期限
    :param Margin_ratio: 保证金比例
    """
    start_beta = - back_test_date - cal_beta_date # beta计算开始日
    end_back = - back_test_date + hold_period

    beta = cal_Beta(data[start_beta:-back_test_date,:]) # 计算beta值

    backtest_period = data[-back_test_date - 1:end_back, :]
    # 根据贝塔计算对冲策略和收益

    Hedge_return, Stock_retrun, Future_retrun = cal_retruns(backtest_period, beta)

    return [Hedge_return,Stock_retrun, Future_retrun]


#*******************************************************************************
data = np.array(pd.read_csv("data/fu_idx_PF_close.csv", index_col="date"))


# 预设值设置
back_test_date = 100 # 回测期限
cal_beta_date = 200 # 贝塔计算期限
hold_period = 5  # 持有期限

# 生成参数配置矩阵
list = []
for i in range(5,back_test_date+1, 5):
    for j in range(5, cal_beta_date, 5):
        for k in range(5, i, 5):
            list.append([i, j , k])

df = pd.DataFrame(list, columns=["test1","test2","test3"])


# 分别对每列进行三项计算
output1 = df.apply(lambda row:future_hedge_design(data, row["test1"],row["test2"],row["test3"]), axis = 1)
b = pd.DataFrame([[x[0],x[1],x[2]] for x in output1], columns=["Hedge_return","Stock_retrun", "Future_retrun"])

output = pd.concat([df, b], axis= 1)
output.columns = ["back_test_date","cal_beta_date","hold_period","Hedge_return","Stock_retrun", "Future_retrun"]
# output.to_csv("data/upgrade_output.csv", index=False)
# output.to_excel("data/upgrade_output.xlsx", index=False)


# 尝试可视化结果
file = pd.read_csv("data/upgrade_output/upgrade_output.csv")
sub_file = file[file["hold_period"] == 5]


x1 = sub_file["back_test_date"]
y1 = sub_file["cal_beta_date"]
z1 = sub_file["Hedge_return"]

fig = plt.figure()
ax = Axes3D(fig)
ax.scatter(x1,y1,z1, c="r", label = "Hedge Return")
ax.legend(loc="beast")

ax.set_xlabel('X label') # 画出坐标轴
ax.set_ylabel('Y label')
ax.set_zlabel('Z label')

plt.show()















