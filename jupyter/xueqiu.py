import requests
import time
import math
import numpy as np
from datetime import date,datetime

def xueqiuJson(url):
    s = requests.session()
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
            'Cookie':'_ga=GA1.2.528987204.1555945543; device_id=3977a79bb79f8dd823919ae175048ee6; s=ds12dcnoxk; __utmz=1.1555945599.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); bid=693c9580ce1eeffbf31bb1efd0320f72_jushvajy; aliyungf_tc=AQAAAOIpumBckAMAiQbzchVmEU+Ji7i7; __utmc=1; xq_a_token.sig=71HQ_PXQYeTyQvRDRGXoyAI8Cdg; xq_r_token.sig=QUTS2bLrXGdbA80soO-wu-fOBgY; snbim_minify=true; acw_tc=2760822d15756229262972757e6f293b44f4b01eff4ceb7a180f0a4c9ed067; Hm_lvt_1db88642e346389874251b5a1eded6e3=1577774083,1577774182,1577774249,1577774257; __utma=1.528987204.1555945543.1577775593.1577826553.72; remember=1; xq_a_token=c44d723738529eb6b274022a320258d92f31cc1e; xqat=c44d723738529eb6b274022a320258d92f31cc1e; xq_r_token=b926ebba0cf9dcf8c01a628b525f93191a24ca0d; xq_is_login=1; u=6625580533; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1577924260'}
    r = s.get(url,headers=headers)
    if r.status_code==200:
        return True,r.json()
    else:
        print(url,r.status_code,r.reason)
        return False,r.reason

def xueqiuK15(code,n=32):
    timestamp = math.floor(time.time()*1000)
    uri = """https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=%s&begin=%s&period=15m&type=before&count=-%d&indicator=kline"""%(code,timestamp,n)
    return xueqiuJson(uri)

#当前是交易时间
def isTransTime():
    to = datetime.today()
    if to.weekday()>=0 and to.weekday()<=4 and to.hour>=9 and to.hour<=15:
        if to.hour==9 and to.minute<45:
            return False
        return True
    return False

#将今日数据写入到k,d中去，成功返回True
def appendTodayK(code,k,d):
    b,K,D = xueqiuK15day(code)
    if b:
        return b,np.vstack((k,[K])),d+((D,),)
    return b,k,d

#以k15为基础给出当日的k数据，成交量为预估
#返回b,[volume,open,high,low,close],date
#同时在这里做一个15分钟的缓存区
k15daycache = {}
def xueqiuK15day(code):
    global k15daycache
    if code in k15daycache:
        cct = k15daycache[code]['time']
        tot = datetime.today()
        if cct.hour==tot.hour and math.floor(cct.minute/15)==math.floor(tot.minute/15):
            data = k15daycache[code]['data']
            return True,data[0],data[1]
    data = xueqiuK15(code,32)
    if len(data)>0:
        if data[0] and data[1] and data[1]['data'] and data[1]['data']['item']:
            items = data[1]['data']['item']
            dd = date.fromtimestamp(items[-1][0]/1000)
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
            
            k15daycache[code] = {'time':datetime.today(),'data':(k,dd)}
            return True,k,dd
    return False,0,0
#自选全部
def xueqiuList():
    uri = """https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json?size=1000&pid=-1&category=1"""
    return xueqiuJson(uri)