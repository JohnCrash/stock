import requests
import time
import math
import numpy as np
from datetime import date,datetime
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

#深交所数据分时
#http://www.szse.cn/api/market/ssjjhq/getTimeData?random=0.9981093803414802&marketId=1&code=000004
#日K
#http://www.szse.cn/api/market/ssjjhq/getHistoryData?random=0.04502169743970663&cycleType=32&marketId=1&code=000004
#上交所日K
#上交所分时
#http://yunhq.sse.com.cn:32041//v1/sh1/line/600651?callback=jQuery112406979082530694531_1581938826571&begin=0&end=-1&select=time%2Cprice%2Cvolume&_=1581938826575
#腾讯证券分时，5分钟，30分钟，日
#http://ifzq.gtimg.cn/appstock/app/kline/mkline?param=sh000001,m60,,320&_var=m60_today&r=0.16306752634257426
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
        
        url = """http://ifzq.gtimg.cn/appstock/app/kline/mkline?param=%s,m5,,%d&_var=m5_today&r=%f"""%(code.lower(),n,random.random())
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
                    for v in k:
                        #0 date , 1 open , 2 close , 3 high , 4 low , 5 volume , 6 ? , 7 ?
                        t = datetime(year=int(v[0][0:4]),month=int(v[0][4:6]),day=int(v[0][6:8]),hour=int(v[0][8:10]),minute=int(v[0][10:12]))
                        K.append((t,float(v[5]),float(v[1]),float(v[3]),float(v[4]),float(v[2])))
                    assert(len(K)==n)
                    return True,K
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
            d = K[0]
            volume = d[1]
            openv = d[2]
            high = d[3]
            low = d[4]
            a = 1
            for i in range(len(K)):
                d = K[i]
                if d[0].minute%15==5:
                    volume = d[1]
                    openv = d[2]
                    high = d[3]
                    low = d[4]
                    a = 1
                else:
                    volume += d[1]
                    high = max(high,d[3])
                    low = min(low,d[4])
                    a += 1
                if d[0].minute%15==0 and a==3:
                    k.append([d[0],volume,openv,high,low,d[5]])
            return b,k
        else:
            mylog.err("qqK15调用qqK5 '%s'返回的数量为%d,请求的数量为%d"%(code,len(K),n*3))
            return False,"qqK15调用qqK5 '%s'返回的数量为%d,请求的数量为%d"%(code,len(K),n*3)
    else:
        return b,K

#新浪财经数据
# True , [(0 timesramp,1 volume,2 open,3 high,4 low,5 close),...]
# False, "Error infomation"
def sinaK15(code,n=32):
    try:
        s = requests.session()
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9'}
        timestramp = math.floor(time.time()*1000)
        url = """https://quotes.sina.cn/cn/api/jsonp_v2.php/var _%s_15_%d=/CN_MarketDataService.getKLineData?symbol=%s&scale=15&ma=no&datalen=%d"""%(code.lower(),timestramp,code.lower(),n)
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
                for v in k:
                    K.append((datetime.fromisoformat(v['day']),float(v['volume']),float(v['open']),float(v['high']),float(v['low']),float(v['close'])))
                assert(len(K)==n)
                return True,K
            else:
                return False,"返回错误或者格式发生变化:"+str(r.text)
        else:
            return False,r.reason
    except Exception as e:
        mylog.err("sinaK15:"+str(code)+"ERROR:"+str(e))
        return False,str(e)

#雪球数据
#返回标准格式
# True , ((timesramp,volume,open,high,low,close),...)
# False, "Error infomation"
def xueqiuK15(code,n=32):
    try:
        timestamp = math.floor(time.time()*1000)
        uri = """https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=%s&begin=%s&period=15m&type=before&count=-%d&indicator=kline"""%(code,timestamp,n)
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

#sina财经作为主下载站点，xueqiu作为备份站点
stockK15Service = [
    {
        "name":u"新浪k15",
        "k15":sinaK15,
        "error":0,
        "success":0
    },
    {
        "name":u"雪球k15",
        "k15":xueqiuK15,
        "error":0,
        "success":0
    },
    {
        "name":u"腾讯k15",
        "k15":qqK15,
        "error":0,
        "success":0
    }
]
current = 0
lock = threading.Lock()
def k15(code,n=32):
    global current
    for i in range(10):
        service = stockK15Service[current]
        b,d = service["k15"](code,n)
        if b:
            service['success'] += 1
            return b,d
        else:
            service['error'] += 1
            lock.acquire()
            if current<len(stockK15Service)-1:
                current+=1
            else:
                current = 0
            lock.release()
    mylog.warn("k15多次尝试下载："+code+" 失败")
    mylog.warn(str(stockK15Service))
    return False,"k15多次尝试下载："+code+" 失败"

#当前是交易时间
def isTransTime():
    to = datetime.today()
    if to.weekday()>=0 and to.weekday()<=4 and to.hour>=9 and to.hour<=14:
        if to.hour==9 and to.minute<30:
            return False
        return True
    return False

#将今日数据写入到k,d中去，成功返回True
def appendTodayK(code,k,d):
    b,K,D = xueqiuK15day(code,lastDayK=k[-1])
    if b:
        if date.today()==D: #返回的日期就是今天
            if type(d)==list:
                rd = d+[(D,)]
            elif type(d)==tuple:
                rd = d+((D,),)
            else:
                mylog.warn('appendTodayK 错误的参数d = ',d,type(d))
            return b,np.vstack((k,[K])),rd
        else:
            return b,k,d
    return b,k,d

#以k15为基础给出当日的k数据，成交量为预估
#返回b,[volume,open,high,low,close],date
#同时在这里做一个15分钟的缓存区
#发现新浪的15分钟深圳成指数据全天求和日线成交量不一致
#使用lastDayDate,lastDayK用于发现这种数据不一致性
def xueqiuK15day(code,lastDayK=None,lastStatus=None):
    b,k15d = shared.fromRedis('TODAY_'+code)
    if b:
        tot = datetime.today()
        cct = k15d['time']
        if cct.hour==tot.hour and math.floor(cct.minute/15)==math.floor(tot.minute/15):
            return True,k15d['data'][0],k15d['data'][1]
    b,v = shared.fromRedis('ISEXPIRSE?')
    if b and v:
        return False,0,0
    b,k = k15(code,32)
    if b:
        dd = date(k[-1][0].year,k[-1][0].month,k[-1][0].day)
        if dd!=date.today():
            shared.toRedis(True,'ISEXPIRSE?',ex=60)
            return False,0,0
        for i in range(len(k)-1,-1,-1):
            it = k[i]
            it_dd = date(it[0].year,it[0].month,it[0].day)
            if dd!=it_dd:
                lasti = i
                break
        #0 volume,1 open,2 high,3 low,4 close
        K = []
        to = datetime.today()
        for i in range(len(k)):
            if k[i][0]<to:
                K.append(k[i][1:])
        yesterday = np.array(K[lasti-15:lasti+1])
        today = np.array(K[lasti+1:])
        if len(today)==0:
            return False,0,0
        i = len(today)
        volume = yesterday[:,0].sum()*today[:,0].sum()/yesterday[0:i,0].sum()
        k = [volume,today[0][1],today[:,2].max(),today[:,3].min(),today[-1][4]]
        #这里对昨天的k15数据计算得到的日线数据和雪球日线数据进行校验
        #=======================================================
        global current
        if lastDayK is not None or lastStatus is not None:
            if lastDayK is not None:
                #下面是通过k15求出昨天的日线数据，然后进行比较
                k15YesterdayK = np.array([yesterday[:,0].sum(),yesterday[0][1],yesterday[:,2].max(),yesterday[:,3].min(),yesterday[-1][4]])
            elif lastStatus is not None:
                #lastStatus =  (0 id , 1 close , 2 volume , 3 volumema20 , 4 macd , 5 energy ,6 volumeJ ,7 bollup ,8 bollmid,9 bolldn,10 bollw)
                k15YesterdayK = np.array([yesterday[:,0].sum(),yesterday[-1][4]])
                lastDayK = np.array([lastStatus[2],lastStatus[1]])
            dev=k15YesterdayK/lastDayK
            if np.abs(dev-1).max()>0.02:
                #如果仅仅是成交量偏差，做偏差纠正处理
                if np.abs(dev[1:]-1).max()<0.02:
                    k[0] = k[0]/dev[0]
                else:
                    mylog.warn(u"'%s' '%s'数据和日线数据不一致"%(stockK15Service[current]['name'],code))
                    mylog.warn(u"    日线数据:%s"%(str(lastDayK)))
                    mylog.warn(u"    k15计算数据:%s"%(str(k15YesterdayK)))
                    mylog.warn(u"    k15原始数据:%s"%(str(yesterday)))
                    mylog.warn(u"    偏差:%s"%(str(dev)))
        #校验处理完成
        #=======================================================
        shared.toRedis({'time':datetime.today(),'data':(k,dd)},'TODAY_'+code,ex=nextdt15()) #到下一个15整点过期
        return True,k,dd
    return False,0,0
#自选全部
def xueqiuList():
    uri = """https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json?size=1000&pid=-1&category=1"""
    return xueqiuJson(uri)