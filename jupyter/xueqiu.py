import requests
import time
import math
import numpy as np
from datetime import date,datetime,timedelta
import shared
import json
import random
import threading
import mylog
import asyncio

class Timer:
    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout) 
        self._callback()

    def cancel(self):
        self._task.cancel()

mylog.init('./download_stock.log')

#如果是在开盘状态则15分钟更新一次数据
def nextdt15():
    t = datetime.today()
    if (t.hour==11 and t.minute>=30) or t.hour==12:#中午休息需要跳过
        return (datetime(t.year,t.month,t.day,13,15,0)-t).seconds+15*60
    return (15-t.minute%15)*60-t.second

def xueqiuJson(url):
    s = requests.session()
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate',
            'Cookie':'_ga=GA1.2.528987204.1555945543; device_id=3977a79bb79f8dd823919ae175048ee6; s=ds12dcnoxk; bid=693c9580ce1eeffbf31bb1efd0320f72_jushvajy; xq_a_token.sig=71HQ_PXQYeTyQvRDRGXoyAI8Cdg; xq_r_token.sig=QUTS2bLrXGdbA80soO-wu-fOBgY; snbim_minify=true; cookiesu=611580616600184; Hm_lvt_1db88642e346389874251b5a1eded6e3=1580196127,1580197850,1580447002,1580630322; remember=1; xq_a_token=0e0638737a1c6fc314110dbcfaca3650f71fce4b; xqat=0e0638737a1c6fc314110dbcfaca3650f71fce4b; xq_r_token=b2004307cb6bd998b245347262380833b61ce0f4; xq_is_login=1; u=6625580533; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1580630785'}
    r = s.get(url,headers=headers)
    if r.status_code==200:
        return True,r.json()
    else:
        return False,r.reason
#腾讯证券 5分钟数据
def qqK5(code,n=96):
    try:
        s = requests.session()
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9'}
        
        url = """http://ifzq.gtimg.cn/appstock/app/kline/mkline?param=%s,m5,,%d&_var=m5_today&r=%f"""%(code.lower(),n+1,random.random())
        r = s.get(url,headers=headers)
        if r.status_code==200:
            """
            m5_today={
                "code":0,
                "msg":"",
                "data":{
                    "sh000001":{
                        "qt":{
                            "sh000001":{
                                该股票信息
                            }
                            "market":["2020-02-17 19:42:01|HK_close_已收盘...."],
                            "zhishu":[]
                            "zjlx":[]
                        }
                        "m5":[
                            ["date例如：202002071055","open","close","high","low","volume",{},""]
                        ] 
                        "prec":"2917.01"                    
                    }
                }
            }
            """
            if len(r.text)>11 and r.text[:9]=="m5_today=":
                m5today = json.loads(r.text[9:])
                if 'data' in m5today and code.lower() in m5today['data'] and 'm5' in m5today['data'][code.lower()]:
                    k = m5today['data'][code.lower()]['m5']
                    K = []
                    today = datetime.today()
                    for v in k:
                        #0 date , 1 open , 2 close , 3 high , 4 low , 5 volume , 6 ? , 7 ?
                        t = datetime(year=int(v[0][0:4]),month=int(v[0][4:6]),day=int(v[0][6:8]),hour=int(v[0][8:10]),minute=int(v[0][10:12]))
                        if t<=today and t.minute%5==0:
                            K.append((t,float(v[5]),float(v[1]),float(v[3]),float(v[4]),float(v[2])))
                    
                    return True,K[-n:]
                return False,"qqK5返回错误或者格式发生变化:"+str(r.text)
            else:
                return False,"qqK5返回错误，没有发现‘m5_today=’:"+str(r.text)
        else:
            return False,r.reason
    except Exception as e:
        mylog.err("qqK5:"+str(code)+"ERROR:"+str(e))
        return False,str(e)

#通过调用qqK5转换而来
def qqK15(code,n=32):
    b,K = qqK5(code,n=(n+1)*3)
    if b:
        if len(K)==(n+1)*3:
            k = []
            mod = K[0][0].minute%15
            if mod==5:
                bi = 0
            elif mod==10:
                bi = 3
            else:
                bi = 1

            for i in range(bi,len(K),3):
                if i+2<len(K):
                    k0 = K[i]
                    k1 = K[i+1]
                    k2 = K[i+2]
                    volume = k0[1]+k1[1]+k2[1]
                    high = max(k0[3],k1[3],k2[3])
                    low = min(k0[4],k1[4],k2[4])
                    k.append([k2[0],volume,k0[2],high,low,k2[5]])
            return b,k[-n:]
        else:
            mylog.err("qqK15调用qqK5 '%s'返回的数量为%d,请求的数量为%d"%(code,len(K),n*3))
            return False,"qqK15调用qqK5 '%s'返回的数量为%d,请求的数量为%d"%(code,len(K),n*3)
    else:
        return b,K

#新浪财经数据
# True , [(0 timesramp,1 volume,2 open,3 high,4 low,5 close),...]
# False, "Error infomation"
def sinaK(code,period,n):
    try:
        s = requests.session()
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9'}
        timestramp = math.floor(time.time()*1000)
        #https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_sh000001_5_1582094915235=/CN_MarketDataService.getKLineData?symbol=sh000001&scale=5&ma=no&datalen=1023
        url = """https://quotes.sina.cn/cn/api/jsonp_v2.php/var _%s_%d_%d=/CN_MarketDataService.getKLineData?symbol=%s&scale=%d&ma=no&datalen=%d"""%(code.lower(),period,timestramp,code.lower(),period,n+1)
        r = s.get(url,headers=headers)
        if r.status_code==200:
            """
            var jsvar =([{"day":"2020-02-13 09:45:00","open":"2927.144","high":"2934.652","low":"2923.232","close":"2934.303","volume":"5111848800"},
            ...}]);
            """
            bi = r.text.find("=([{")
            ei = r.text.find("}]);")
            if bi>0 and ei>0 and ei>bi and ei+2<len(r.text):
                k = json.loads(r.text[bi+2:ei+2])
                K = []
                today = datetime.today()
                for v in k:
                    t = datetime.fromisoformat(v['day'])
                    if t<=today:
                        K.append((t,float(v['volume']),float(v['open']),float(v['high']),float(v['low']),float(v['close'])))
                return True,K[-n:]
            else:
                return False,"返回错误或者格式发生变化:"+str(r.text)
        else:
            return False,r.reason
    except Exception as e:
        mylog.err("sinaK15:"+str(code)+"ERROR:"+str(e))
        return False,str(e)

def sinaK15(code,n=32):
    return sinaK(code,15,n)
def sinaK5(code,n=96):
    return sinaK(code,5,n)
#雪球数据
# True , ((timesramp,volume,open,high,low,close),...)
# False, "Error infomation"
def xueqiuK(code,period,n):
    try:
        timestamp = math.floor(time.time()*1000)
        uri = """https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=%s&begin=%s&period=%sm&type=before&count=-%d&indicator=kline"""%(code,timestamp,str(period),n)
        b,dd = xueqiuJson(uri)
        if b:
            """
            {
                'data':{
                    'symbol':code,
                    'column':[
                        'timestamp',
                        'volume',
                        'open',
                        'high',
                        'low',
                        'close',
                        'chg',
                        'percent',
                        'turnoverrate',
                        'amount',
                        'volume_post',
                        'amount_post'
                    ],
                    'item':[
                        [timestamp,volume,....]
                    ]
                }
            }
            """
            K = []
            d = dd['data']
            for i in range(len(d['column'])):
                if d['column'][i]=='open':
                    open_inx = i
                elif d['column'][i]=='close':
                    close_inx = i
                elif d['column'][i]=='high':
                    high_inx = i
                elif d['column'][i]=='low':
                    low_inx = i
                elif d['column'][i]=='timestamp':
                    timestamp_inx = i
                elif d['column'][i]=='volume':
                    volume_inx = i
            for v in d['item']:
                K.append((datetime.fromtimestamp(v[timestamp_inx]/1000),v[volume_inx],v[open_inx],v[high_inx],v[low_inx],v[close_inx]))
            assert(len(K)==n)
            return True,K
        else:
            return b,d
    except Exception as e:
        mylog.err("xueqiuK15:"+str(code)+"ERROR:"+str(e))
        return False,str(e) 
#返回标准格式
# True , ((timesramp,volume,open,high,low,close),...)
# False, "Error infomation"
def xueqiuK15(code,n=32):
    return xueqiuK(code,15,n)
def xueqiuK5(code,n=96):
    return xueqiuK(code,5,n)

stockK5Service = [
    {
        "name":u"新浪k5",
        "cb":sinaK5,
        "error":0,
        "success":0,
        "total":0,#总用时
        "avg":0 #平均用时
    },
    {
        "name":u"雪球k5",
        "cb":xueqiuK5,
        "error":0,
        "success":0,
        "total":0,
        "avg":0    
    },
    {
        "name":u"腾讯k5",
        "cb":qqK5,
        "error":0,
        "success":0,
        "total":0,
        "avg":0         
    }
]
stockK15Service = [
    {
        "name":u"新浪k15",
        "cb":sinaK15,
        "error":0,
        "success":0,
        "total":0,
        "avg":0         
    },
    {
        "name":u"雪球k15",
        "cb":xueqiuK15,
        "error":0,
        "success":0,
        "total":0,
        "avg":0         
    },
    {
        "name":u"腾讯k15",
        "cb":qqK15,
        "error":0,
        "success":0,
        "total":0,
        "avg":0         
    }
]
def logServiceState():
    mylog.warn("==============stockK15Service=============")
    for it in stockK15Service:
        mylog.warn("%s error:%d success:%d avg:%fms"%(it['name'],it['error'],it['success'],1000*it['avg']))
    mylog.warn("==============stockK5Service=============")
    for it in stockK5Service:
        mylog.warn("%s error:%d success:%d avg:%fms"%(it['name'],it['error'],it['success'],1000*it['avg']))

#下载K数据，返回True/False,[(timesramp,volume,open,high,low,close)...],source
def getK(code,period,n):
    service = None
    if period==5:
        service = stockK5Service
    elif period==15:
        service = stockK15Service
    if service is not None:
        for i in range(10):
            current = random.randint(0,len(service)-1)
            t0 = time.time()
            b,d = service[current]['cb'](code,n)
            if b:
                service[current]['success'] +=1
                service[current]['total'] += time.time()-t0
                service[current]['avg'] = service[current]['total']/service[current]['success']
                return b,d,service[current]['name']
            else:
                service['error'] += 1
    return False,0,0

#返回下一个正确的时间k日期
def nextKDate(t,period):
    if t.hour<15:
        if t.hour==11 and t.minute==30:
            return datetime(t.year,t.month,t.day,13,period)
        else:
            return t+timedelta(minutes=period)
    #返回下一个交易日的第一k时间戳
    nt = t+timedelta(days=1 if t.weekday()!=4 else 3)
    return datetime(nt.year,nt.month,nt.day,9,35 if period==5 else 45)

def isEqK(k0,k1):
    for i in range(5):
        if abs(k0[i]/k1[i]-1)>0.02:
            return False
    return True

#产生一个日期表便于查找
k5date = []
for i in [9,10,11,13,14,15]:
    if i in [10,13,14]:
        for m in range(0,60,5):
            k5date.append((i,m))
    elif i==9:
        for m in range(35,60,5):
            k5date.append((i,m))
    elif i==11:
        for m in range(5,35,5):
            k5date.append((i,m))
    else:
        k5date.append((i,0))
k15date = []
for i in [9,10,11,13,14,15]:
    if i in [10,13,14]:
        for m in range(0,60,15):
            k15date.append((i,m))
    elif i==9:
        for m in range(35,60,15):
            k15date.append((i,m))
    elif i==11:
        for m in range(5,35,15):
            k15date.append((i,m))
    else:
        k15date.append((i,0))

#计算从hour,minute到当前时间存在多少个k点
def from2now(hour,minute,period):
    n = 0
    m = k15date if period==15 else k5date
    today = datetime.today()
    for d in m[period]:
        if (d[0]>hour or (d[0]==hour and d[1]>minute)) and (today.hour>d[0] or (today.hour==d[0] and today.minute<=d[1])):
            n += 1
    return n

#返回指定代码的k线数据
# True , np.array((timesramp,volume,open,high,low,close),...),[(timesramp,)...] 保持和loadKline相同的数据结构
# False, "Error infomation"
#缓存区保持两天的数据量
def K(code,period,n):
    cacheName = "k%s_%s"%(str(period).lower(),code.lower())
    #cache = {'k':np.array((volume,open,high,low,close),...),'date':[(timesramp,)...],'base':} base是最初的数据来源
    b,cache = shared.fromRedis(cacheName)
    if b and len(cache['k'])>=n and nextKDate(cache['date'][-1][0],period)>datetime.today(): #存在缓存并且没有新的数据直接返回
        return b,cache['k'][-n:],cache['date'][-n:]
    if b: #如果有数据那么仅仅下载最新数据和部分校验用数据
        base = cache['base']
        #还需要下载多少数据
        if datetime.today().day!=cache['date'][-1][0].day: #缓存是昨天的数据
            #从9:30到现在的全部数据
            dn = from2now(9,30,period)+2
        else: #缓存是今天数据
            t = cache['date'][-1][0]
            dn = from2now(t.hour,t.minute,period)+2
    elif n<15*16/period:
        dn = int(15*16/period)
    else:
        dn = n
    a,k,s = getK(code,period,dn)
    K = []
    if a and b:
        #校验重叠区域数据,合并数据
        oldK = cache['k']
        d = cache['date']
        bi = -1
        for i in range(len(k)-1,-1,-1): #找到重叠部分
            if k[i][0]==d[-1][0]:
                bi = i
        #校验接缝处的数据
        if bi<0 or not isEqK(oldK[-1],k[bi]):
            mylog.err("'%s' %s base='%s' 和 '%s'存在%d处存在较大差异"%(code,str(period),base,s,bi))
            mylog.err("cacheK:"+str(oldK))
            mylog.err("caheDate:"+str(d))
            mylog.err("k:"+str(k))
            return False,0,0
        for i in range(bi+1,len(k)):
            v = k[i]
            K.append((v[1],v[2],v[3],v[4],v[5]))
            d.append((v[0],))
        k = np.vstack((oldK,np.array(K)))
    elif a:
        base = s
        for v in range(len(k)):
            K.append((v[1],v[2],v[3],v[4],v[5]))
            d.append((v[0],))
        k = np.array(K)
    else:
        mylog.err("'%s' %s 下载时出错"%(code,str(period)))
        logServiceState()
        return False,0,0

    shared.toRedis(cacheName,{'k':k,'date':d,'base':base},ex=24*3600)
    return True,k[-n:],d[-n:]

#当前是交易时间
def isTransTime():
    to = datetime.today()
    if to.weekday()>=0 and to.weekday()<=4 and to.hour>=9 and to.hour<=14:
        if to.hour==9 and to.minute<30:
            return False
        return True
    return False

#将下载数据附加在k,d数据上
def appendK(code,period,k,d):
    if period==5 or period==15:
        b,nk,nd = K(code,period,32 if period==15 else 96)
    elif period=='d':
        b,nk,nd = xueqiuKday(code,15)
        #这里对昨天的k15数据计算得到的日线数据和雪球日线数据进行校验
        #=======================================================
        if len(k)>0:
            dev = nk[-1]/k[-1]
            if np.abs(dev-1).max()>0.02:
                #如果仅仅是成交量偏差，做偏差纠正处理
                if np.abs(dev[0]-1).max()>0.02:
                    nk[0] = nk[0]/dev[0]
                else:
                    mylog.warn(u"'%s' '%s'数据和日线数据不一致"%(code))
                    mylog.warn(u"    日线数据:%s,%s"%(str(k[-1]),str(d[-1])))
                    mylog.warn(u"    k15计算数据:%s,%s"%(str(nk[-1]),str(nd[-1])))
                    mylog.warn(u"    偏差:%s"%(str(dev)))
        #校验处理完成
        #=======================================================        
    else:
        return False,k,d
    if b:
        bi = -1
        for i in range(len(nd)-1,-1,-1):
            if d[-1][0]==nd[i][0]:
                bi = i
        if bi!=-1:
            for i in range(bi+1,len(nd)):
                d.append(nd[i])
            if len(d)>0:
                return b,np.vstack((k,nk[bi+1:,:])),d
    return b,k,d

#以k15为基础给出当日的k数据，成交量为预估
#返回b,np.array([volume,open,high,low,close]),[(date,)...]
#同时在这里做一个15分钟的缓存区
#发现新浪的15分钟深圳成指数据全天求和日线成交量不一致
#使用lastDayDate,lastDayK用于发现这种数据不一致性
def xueqiuKday(code,period):
    b,k,d = K(code,period,32)
    if b:
        dd = date(d[-1][0].year,d[-1][0].month,d[-1][0].day)
        for i in range(len(k)-1,-1,-1):
            it = d[i][0]
            it_dd = date(it[0].year,it[0].month,it[0].day)
            if dd!=it_dd:
                lasti = i
                break
        #0 volume,1 open,2 high,3 low,4 close
        yesterday = k[lasti-period:lasti+1,:]
        today = k[lasti+1:,:]
        if len(today)==0:
            return False,0,0
        i = len(today)
        volume = yesterday[:,0].sum()*today[:,0].sum()/yesterday[0:i,0].sum()

        return True,np.array([volume,today[0][1],today[:,2].max(),today[:,3].min(),today[-1][4]]),(dd,)
    return False,0,0

#自选全部
def xueqiuList():
    uri = """https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json?size=1000&pid=-1&category=1"""
    return xueqiuJson(uri)