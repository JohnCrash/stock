import requests
import time
import math
import numpy as np
from datetime import date,datetime
import shared

def xueqiuJson(url):
    s = requests.session()
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate',
            'Cookie':'_ga=GA1.2.528987204.1555945543; device_id=3977a79bb79f8dd823919ae175048ee6; s=ds12dcnoxk; bid=693c9580ce1eeffbf31bb1efd0320f72_jushvajy; xq_a_token.sig=71HQ_PXQYeTyQvRDRGXoyAI8Cdg; xq_r_token.sig=QUTS2bLrXGdbA80soO-wu-fOBgY; snbim_minify=true; cookiesu=611580616600184; Hm_lvt_1db88642e346389874251b5a1eded6e3=1580196127,1580197850,1580447002,1580630322; remember=1; xq_a_token=0e0638737a1c6fc314110dbcfaca3650f71fce4b; xqat=0e0638737a1c6fc314110dbcfaca3650f71fce4b; xq_r_token=b2004307cb6bd998b245347262380833b61ce0f4; xq_is_login=1; u=6625580533; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1580630785'}
    for i in range(10):
        try:
            r = s.get(url,headers=headers)
            if r.status_code==200:
                return True,r.json()
            else:
                print(url,r.status_code,r.reason)
                return False,r.reason
        except Exception as e:
            print('第',i,'次尝试',e)

#新浪财经数据
def sinaK15Native(code,n=32):
    s = requests.session()
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
               'Accept-Encoding': 'gzip, deflate',
               'Accept-Language': 'zh-CN,zh;q=0.9'}
    timestramp = math.floor(time.time()*1000)
    url = """https://quotes.sina.cn/cn/api/jsonp_v2.php/var _%s_15_%d=/CN_MarketDataService.getKLineData?symbol=%s&scale=15&ma=no&datalen=%d"""%(code.lower(),timestramp,code.lower(),n)
    print(url)
    for i in range(10):
        try:
            r = s.get(url,headers=headers)
            if r.status_code==200:
                return True,r
            else:
                print(url,r.status_code,r.reason)
                return False,r.reason
        except Exception as e:
            print('第',i,'次尝试',e)    
    return False,None
#雪球数据
def xueqiuK15(code,n=32):
    timestamp = math.floor(time.time()*1000)
    uri = """https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=%s&begin=%s&period=15m&type=before&count=-%d&indicator=kline"""%(code,timestamp,n)
    return xueqiuJson(uri)

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
    b,K,D = xueqiuK15day(code)
    if b:
        if date.today()==D: #返回的日期就是今天
            if type(d)==list:
                rd = d+[(D,)]
            elif type(d)==tuple:
                rd = d+((D,),)
            else:
                print('appendTodayK 错误的参数d = ',d,type(d))
            return b,np.vstack((k,[K])),rd
        else:
            return b,k,d
    return b,k,d

#以k15为基础给出当日的k数据，成交量为预估
#返回b,[volume,open,high,low,close],date
#同时在这里做一个15分钟的缓存区
def xueqiuK15day(code):
    b,k15d = shared.fromRedis('TODAY_'+code)
    if b:
        tot = datetime.today()
        cct = k15d['time']
        if cct.hour==tot.hour and math.floor(cct.minute/15)==math.floor(tot.minute/15):
            return True,k15d['data'][0],k15d['data'][1]
    b,v = shared.fromRedis('ISEXPIRSE?')
    if b and v:
        return False,0,0
    data = xueqiuK15(code,32)
    if len(data)>0:
        if data[0] and data[1] and data[1]['data'] and data[1]['data']['item']:
            items = data[1]['data']['item']
            dd = date.fromtimestamp(items[-1][0]/1000)
            if dd!=date.today():
                shared.toRedis(True,'ISEXPIRSE?',ex=60)
                return False,0,0
            for i in range(len(items)-1,-1,-1):
                it = items[i]
                if dd!=date.fromtimestamp(it[0]/1000):
                    lasti = i
                    break
            #0 timestamp,1 volume,2 open,3 high,4 low,5 close,chg,....
            yesterday = np.array(items[lasti-15:lasti+1])
            today = np.array(items[lasti+1:])
     
            #这里要预测今天的volume
            i = len(today)
            volume = yesterday[:,1].sum()*today[:,1].sum()/yesterday[0:i,1].sum()
            k = [volume,today[0][2],today[:,3].max(),today[:,4].min(),today[-1][5]]
            
            shared.toRedis({'time':datetime.today(),'data':(k,dd)},'TODAY_'+code,ex=15*60) #15分钟后过期
            return True,k,dd
    return False,0,0
#自选全部
def xueqiuList():
    uri = """https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json?size=1000&pid=-1&category=1"""
    return xueqiuJson(uri)