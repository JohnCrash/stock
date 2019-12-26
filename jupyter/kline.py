import stock

"""kline 图显示"""
"""
config {
    ma : [5,10,20,...]
    kdj : n
    volume : True or False
    macd : True or False
    boll : n
    kdate : 日期表
    vlines : {} 竖线
    figsize : (w,h)
    debug : True or False 打印调试信息
}
"""
class Plote:
    def __init__(self,kline,config={"boll":20,"macd":True,"figsize":(28,16),"debug":False}):
        self._k = kline
        self._config = config
    
    def show(self):
        print(self._k)

k = 1
p = Plote(k)
p.show()