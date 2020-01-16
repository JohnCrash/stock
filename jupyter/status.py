"""
对所有股票进行计算
计算器日macd，周macd，日能量，周能量，日成交量kdJ,周成交量kdJ
算法是增量优化的，每次运行仅仅计算增加的部分
"""
import numpy as np
import stock

def update_status():
    stock.opendb()
    stock.query('select date from kd_xueqiu where id=8828 order by date desc limit 1')
    stock.closedb()