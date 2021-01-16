import random
import json
from ipywidgets.widgets.widget_selection import Dropdown
import numpy as np
from IPython.display import display,Markdown
import ipywidgets as widgets
from ipywidgets import Layout, Button, Box
from datetime import date,datetime,timedelta
import matplotlib.pyplot as plt
from . import stock
from . import xueqiu
from . import kline
from . import shared

box_layout = Layout(display='flex',
                flex_flow='wrap',
                align_items='stretch',
                border='solid',
                width='100%')

ETFs = [
    'SH510300', #沪深300ETF
    'SH510050', #上证50ETF
    'SZ159949', #创业板50
    'SH588000', #科创板50ETF
    'SZ159995', #芯片
    'SZ159997', #电子ETF
    'SH515980', #人工智能
    'SH512720', #计算机
    'SZ159994', #5GETF
    'SH512660', #军工
    'SH515700', #新能源车ETF
    'SH512580', #环保
    'SH515790', #光伏
    'SH512800', #银行
    'SH512000', #券商
    'SZ159992', #创新药
    'SH512010', #医药ETF
    'SH512170', #医疗ETF
    "SZ159825", #农业ETF
    'SH512690', #酒
    'SH510150', #消费ETF
    'SZ159996', #家电
    'SH512980', #传媒ETF
    'SH512400', #有色金属ETF
    'SH512580', #环保
    'SH512200', #房地产
    "SH515210", #钢铁
    "SH515220",  #煤炭
    "SH603986", #兆易创新
    "SZ002371", #北方华创
    "SH600584", #长电科技
    "SH603160",#汇顶科技
    "SH688981", #中芯国际-U
    "SZ000725", #京东方A
    "SZ002475", #立讯精密
    "SZ002241",#歌儿股份
    "SH603501",#韦尔股份
    "SZ000063", #中兴通信
    "SZ002230", #科大讯飞
    "SZ002415", #海康威视
    "SZ002049", #紫光国微
    "SH601633", #长城汽车
    "SZ002594", #比亚迪
    "SZ000625", #长安汽车
    "SH600104", #上汽集团
    "SZ300750",  #宁德时代
    "SH600030", #中信证券
    "SH600031",#三一重工
    "SZ000425",#徐工
    "SH601088",#中国神华
    "SH600585", #海螺水泥
    "SH600720",#祁连山
    "SZ000333",#美的
    "SZ000651",#格力
    "SZ000858",#五粮液
    "SH600809", #山西汾酒
    "SZ000568",#泸州老窖
    "SH600276",#恒瑞医药
    "SH600196",#复兴医药
    "SZ300122",#智飞生物
    "SZ300015",#爱尔眼科
    "SH601899",#紫金矿业
    "SZ000878",#云南铜业
    "SH600887"#伊利股份    
]

def savegame(data):
    #将最近的游戏数据记录到redis中缓存，当发现存入的是另一局游戏的时候才将redis中的数据存入数据库
    b,d = shared.fromRedis('gamedata')
    if b and d['id']!=data['id']:
        #编码成json然后存入数据库
        dj = json.dumps(d)
        stock.execute("""insert into game (game) values ('%s')"""%(dj))
    shared.toRedis(data,'gamedata')

def play(code=None,period=15,figsize=(32,15)):
    random.seed()
    if code is None:
        i = random.randint(0,len(ETFs)-1)
        code = ETFs[i]
    
    transpos = [] #交易点
    def mydraw(self,axs,bi,ei):
        nonlocal firstBuyPrice
        if firstBuyPrice is not None:
            axs[0].axhline(y=firstBuyPrice,color='green',linestyle='--')
    K = kline.Plote(code,period,config={'index':True,'disabledate':True,'bigma20':True,'boll':20,'flow':True,'macd':True,'cb':mydraw},mode='normal',transpos=transpos)
    o = K._k[0,4]
    K._k[:,1:]/=o
    bi = random.randint(0,int(len(K._k)/3))
    ei = bi+160
    money = 1 #现金数量
    hold = 0 #持股数量
    hold2 = 0 #持有备买数量
    hold2price = 0 #备买持股价格
    hold2i = None
    price = 0 #持股成本
    Ops = [] #操作序列,(时间戳，0买1卖，买入的钱数或者卖出的股数) 默认取时间戳对应的收盘价作为交易价格
    ttime = None #定时器
    savedata = {
        "id": random.randint(0,999999),#每局游戏有不一样的id
        "code":K._company[1],
        "name":K._company[2],
        "period":period,
        "op":Ops
    }
    
    """
    游戏存储
    """
    buyButton = widgets.Button(description="买入",layout=Layout(width='48px'))
    sellButton = widgets.Button(description="卖出",layout=Layout(width='48px'))
    passButton = widgets.Button(description=">",layout=Layout(width='48px'))
    pass2Button = widgets.Button(description=">>",layout=Layout(width='48px'))
    pass1sButton = widgets.Button(description="1",layout=Layout(width='48px')) #1秒
    pass3sButton = widgets.Button(description="3",layout=Layout(width='48px')) #3秒
    pass5sButton = widgets.Button(description="5",layout=Layout(width='48px')) #5秒
    passedButton = widgets.Button(description="||",layout=Layout(width='48px')) #暂定
    printButton = widgets.Button(description="print",layout=Layout(width='48px'))
    replayButton = widgets.Button(description="重新开始",layout=Layout(width='96px'))
    buy2Button = widgets.Button(description="备买",layout=Layout(width='48px')) #备用资金买入，当前仓位一半 @该策略是为了提供战胜100%持仓的方法
    sell2Button = widgets.Button(description="备卖",layout=Layout(width='48px'))#将备用资金买入的卖出 @备用资金买入持有时间不能超过3天
    opDropdown = widgets.Dropdown(
    options=['25%','50%','100%'],
    value='100%',
    description='操作仓位',
    layout=Layout(display='block',width='160px'),
    disabled=False)
    posLabel = widgets.HTML(value="<b>0%</b>",description='仓位:')
    rateLabel = widgets.HTML(value="<b>0%</b>",description='盈利:')
    rate2Label = widgets.HTML(value="<b>0%</b>",description='一直持有:')
    box = Box(children=[buyButton,sellButton,opDropdown,buy2Button,sell2Button,passButton,pass2Button,passedButton,pass1sButton,pass3sButton,pass5sButton,posLabel,rateLabel,rate2Label,printButton,replayButton],layout=box_layout)
    output = widgets.Output()
    output2 = widgets.Output()
    
    firstBuyPrice = None
    def updateValue():
        posLabel.value = "<b>%.2f%%<b>"%(100*hold*K._k[ei-1,4]/(hold*K._k[ei-1,4]+money))
        m = hold*K._k[ei-1,4]+money
        rateLabel.value = "<b>%.2f%%<b>"%(100*(m-1))
        if firstBuyPrice is not None:
            v = (K._k[ei-1,4]-firstBuyPrice)/firstBuyPrice
            rate2Label.value = "<b>%.2f%%<b>"%(100*v)

    def update():
        nonlocal bi,ei,money,hold2,hold2price,hold2i
        n = 12*4*3*5/period
        if hold2>0 and hold2i is not None and (ei-hold2i>=n):
            orate = 100*(hold*K._k[ei-1,4]+money-1) #当前盈利
            #备份仓位持仓超时需要平到加入的备份仓位
            money += hold2*(K._k[ei-1,4]-hold2price)
            hold2 = 0
            hold2price = 0
            hold2timestamp = None
            nrate = 100*(hold*K._k[ei-1,4]+money-1)-orate #增加的盈利
            transpos.append(('平%.2f%%'%(nrate),1,ei-1))
        #更新按键状态
        if money==0:
            buyButton.disabled = True
        else:
            buyButton.disabled = False
        if hold==0:
            sellButton.disabled = True
        else:
            sellButton.disabled = False
        if ttime is None:
            passedButton.disabled = True
        else:
            passedButton.disabled = False
        if hold2==0 and hold>0:
            buy2Button.disabled = False
        else:
            buy2Button.disabled = True
        if hold2>0:
            sell2Button.disabled = False
        else:
            sell2Button.disabled = True
        updateValue()
        with output2:
            K.showKline(bi,ei,figsize=figsize)    
        
    def get_opvalue():
        nonlocal opDropdown
        return float(opDropdown.value[:-1])/100
    
    def onBuy(e):
        nonlocal money,hold,bi,ei,K,price,Ops,savedata,firstBuyPrice
        if money > 0:
            r = get_opvalue()
            v = (money*r)/K._k[ei-1,4] #买入的股的数量
            Ops.append((stock.timeString(K._date[ei-1][0]),0,money*r)) #存盘数据
            price = (price*hold + K._k[ei-1,4]*v)/(hold+v) #计算新的持仓成本
            hold += v
            money = money*(1-r)
            
            if firstBuyPrice is None:
                firstBuyPrice = K._k[ei-1,4]
            transpos.append(('买',0,ei-1))
            savegame(savedata)
            update()

    buyButton.on_click(onBuy)
    def onBuy2(e):
        nonlocal money,hold,bi,ei,K,price,Ops,savedata,firstBuyPrice,hold2,hold2price,hold2i
        if hold>0 and hold2==0: #持有但是没有备份买入
            hold2 = hold/2 #买入的股的数量
            hold2price = K._k[ei-1,4]
            hold2i = ei-1
            m = hold2/K._k[ei-1,4]
            Ops.append((stock.timeString(K._date[ei-1][0]),0,m)) #存盘数据
            transpos.append(('备买',0,ei-1))
            savegame(savedata)
            update()

    buy2Button.on_click(onBuy2)

    def onSell(e):
        nonlocal money,hold,bi,ei,K,price,Ops,savedata
        if hold>0:
            r = get_opvalue()
            money += (hold*r)*K._k[ei-1,4]
            Ops.append((stock.timeString(K._date[ei-1][0]),1,hold*r)) #存盘数据
            hold = hold*(1-r)
            transpos.append(('卖',1,ei-1))
            savegame(savedata)
            update()
    sellButton.on_click(onSell)

    def onSell2(e):
        nonlocal money,hold,bi,ei,K,price,Ops,savedata,hold2,hold2price,hold2i
        if hold2>0:
            orate = 100*(hold*K._k[ei-1,4]+money-1) #当前盈利
            money += hold2*(K._k[ei-1,4]-hold2price)
            Ops.append((stock.timeString(K._date[ei-1][0]),1,hold2)) #存盘数据
            hold2 = 0
            hold2price = 0
            hold2i = None

            #计算盈利增加或者减少的百分比
            nrate = 100*(hold*K._k[ei-1,4]+money-1)-orate
            transpos.append(('备卖%.2f%%'%(nrate),1,ei-1))
            savegame(savedata)
            update()

    sell2Button.on_click(onSell2)
    step = 1
    def onPass(e):
        nonlocal bi,ei,K,step
        if ei+1<len(K._k):
            bi+=1
            ei+=1
            step = 1
            update()
    passButton.on_click(onPass)
    def onPass2(e):
        nonlocal bi,ei,K,step
        if ei+4<len(K._k):
            bi+=4
            ei+=4
            step = 4
            update()    
    pass2Button.on_click(onPass2)

    def autoforward(t):
        tname = 'game_autoforward'
        nonlocal ttime
        def doforward():
            nonlocal bi,ei,K,step
            if ei+4<len(K._k):
                bi+=step
                ei+=step
                update()
                ttime = xueqiu.setTimeout(t,doforward,tname)
        ttime = xueqiu.setTimeout(t,doforward,tname)

    def onAutoUpdate(e): #自动更新
        autoforward(e.t)
    pass1sButton.t = 1
    pass3sButton.t = 3
    pass5sButton.t = 5
    pass5sButton.on_click(onAutoUpdate)
    pass3sButton.on_click(onAutoUpdate)
    pass1sButton.on_click(onAutoUpdate)
    def onPassed(e): #停止自动
        nonlocal ttime
        if ttime is not None:
            xueqiu.cancelTimeout(ttime)

    passedButton.on_click(onPassed)

    def onPrint(e):
        nonlocal savedata
        print(savedata)
    printButton.on_click(onPrint)

    def onReplay(e):
        nonlocal bi,ei,money,hold2price,hold,hold2,hold2i,price,ttime
        Ops.clear()
        transpos.clear()
        money = 1
        hold = 0
        hold2 = 0
        hold2price = 0
        hold2i = None
        firstBuyPrice = None
        price = 0
        if ttime is not None:
            xueqiu.cancelTimeout(ttime)        
        ttime = None
        savedata['id']= random.randint(0,999999)
        bi = random.randint(0,int(len(K._k)/3))
        ei = bi+160
        update()
    replayButton.on_click(onReplay)
    display(box,output,output2)
    update()