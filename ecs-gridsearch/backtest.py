from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from datetime import datetime
import json
import numpy as np
import pandas as pd
import os.path
import sys

import backtrader as bt

class MyStrategy(bt.Strategy):
    ## 全局参数
    params=(('fastmaperiod', 10),
            ('slowmaperiod', 30),
            ('printlog', False),)

    ## 策略初始化
    def __init__(self):

        # 初始化交易指令、买卖价格和手续费
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # 添加移动均线指标。Backtrader 集成了 talib，可以自动算出一些常见的技术指标
        self.fastma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.fastmaperiod)
        self.slowma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.slowmaperiod)
        
    ## 策略核心逻辑
    def next(self):
        # 记录收盘价
#         self.log('收盘价：%.2f' % self.datas[0].close[0])
        if self.order: # 检查是否有指令等待执行
            return
        # 检查是否持仓   
        if not self.position: # 如果没有持仓
            # 快线上穿慢线，执行买入
            if self.fastma[0] > self.slowma[0]:
                self.log('买入委托：%.2f' % self.datas[0].close[0])
                #执行买入
                self.size = int(self.broker.cash / self.datas[0].close[0])
                self.order = self.buy(size=self.size)
        else: # 
            # 快线下穿慢线，执行卖出
            if self.fastma[0] < self.slowma[0]:
                self.log('卖出委托：%.2f' % self.datas[0].close[0])
                #执行卖出
                self.order = self.sell(size=self.size)

    ## 4、日志记录
    # 交易记录日志（可选，默认不输出结果）
    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()},{txt}')

    # 记录交易执行情况（可选，默认不输出结果）
    def notify_order(self, order):
        # 如果 order 为 submitted/accepted，返回空
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 如果 order 为 buy/sell executed，报告价格结果
        if order.status in [order.Completed]: 
            if order.isbuy():
                self.log(f'买入：\n价格：%.2f,\
                交易金额：-%.2f,\
                手续费：%.2f' % (order.executed.price, order.executed.value, order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(f'卖出:\n价格：%.2f,\
                交易金额：%.2f,\
                手续费：%.2f' % (order.executed.price, order.executed.price*self.size, order.executed.comm))
            self.bar_executed = len(self) 

        # 如果指令取消/交易失败, 报告结果
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('交易失败')
        self.order = None

    # 记录交易收益情况（可省略，默认不输出结果）
    def notify_trade(self,trade):
        if not trade.isclosed:
            return
        self.log(f'策略收益：\n毛收益 {trade.pnl:.2f}, 净收益 {trade.pnlcomm:.2f}')

    # 回测结束后输出结果（可省略，默认输出结果）
    def stop(self):
        self.log('(MA均线： %2d日  %2d日) 期末总资金 %.2f' %
                 (self.params.fastmaperiod, self.params.slowmaperiod, self.broker.getvalue()), doprint=True)


if __name__ == '__main__':
    # 创建 Cerebro 对象
    cerebro = bt.Cerebro()

    df = pd.read_csv('/home/environment/data.csv')
    df.set_index('tradedate', inplace=True)
    
    # 创建 Data Feed
    df.index = pd.to_datetime(df.index)
    start = df.index[0]
    end = df.index[-1]
    print(start, '-', end)
    data = bt.feeds.PandasData(dataname=df, fromdate=start, todate=end)
    # 将 Data Feed 添加至 Cerebro
    cerebro.adddata(data)

    # 添加策略 Cerebro
    with open('/home/environment/input/params.json', 'r') as fin:
        params = json.load(fin)
    cerebro.addstrategy(MyStrategy, fastmaperiod=params['fastmaperiod'], slowmaperiod=params['slowmaperiod'], printlog=True)
    
    # 设置初始资金
    cerebro.broker.setcash(100000.0)
    # 设置手续费为万二
    cerebro.broker.setcommission(commission=0.0002) 

    # 在开始时 print 初始账户价值
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # 运行回测流程
    cerebro.run()

    # 在结束时 print 最终账户价值
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # 输出最终账户价值和收益率
    output = {
        "value": cerebro.broker.getvalue(), 
        "return": float(cerebro.broker.getvalue())/1e5 - 1
    }
    with open('/home/environment/output/output.json', 'w') as fout:
        json.dump(output, fout)
