计算公式详见Hull《期权、期货与其他衍生品》第九版第六章中 曲率调整 和 利用欧洲美元期货延长LIBOR零息收益曲线
脚本和计算过程中有两个已知错误点，请周知：
（1）曲率调整中sigma的计算（未学到），采取了书中的值0.012，需进行实际调整；
（2）libor的计算未考虑实际日期，仅以月份作为标记（简化过程）；

同时需注意：
根据FCA说明，libor将在2021年底退出市场，对应的美元LIBOR将用芝商所（CME)的SOFR期货品种代替，该期货目前有1月和3月，报价方式与欧洲美元报价方式相同。