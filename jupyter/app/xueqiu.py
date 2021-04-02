from . import category
import requests
import time
import math
import numpy as np
from datetime import date,datetime,timedelta
from . import shared
import json
import copy
import uuid
import random
import threading
from . import stock
from . import mylog
import asyncio
from . import config

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

gtimer = None

def gtimerLoop():
    global gtimer
    deletes = []
    gt = gtimer
    for v in gt:
        timer = gt[v]
        if timer is not None and 't' in timer and 'func' in timer:
            timer['t'] += 1
            if timer['t']>= timer['dt']:
                gt[v] = None
                try:
                    timer['func']()
                except:
                    pass
                if gt[v] is None:
                    deletes.append(v)
    for v in deletes:
        del gt[v]
    Timer(1,gtimerLoop)

if gtimer is None:
    gtimer = {}
    gtimerLoop()
"""
设置周期调用函数func,周期为dt,命名name
当设置func=None时,则取消该周期调用
"""
def setTimeout(dt,func,name):
    global gtimer
    gtimer[name] = {
        'name' : name,
        'dt' : int(dt),
        'func' : func,
        't' : 0
    }
    return gtimer[name]

def cancelTimeout(t):
    global gtimer
    if 'name' in t and t['name'] in gtimer:
        del gtimer[t['name']]
def clearTimer():
    global gtimer
    gtimer = {}

log = mylog.init('download_stock.log',name='xueqiu')
xueqiu_cookie = ""

#获取xueqiu网站的cookie
def xueqiuCookie():
    s = requests.session()
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate'}
    r = s.get('https://xueqiu.com/',headers=headers)    
    if r.status_code==200:
        cookie = ""
        for it in r.cookies:
            if cookie != "":
                cookie += "; "
            cookie += "%s=%s"%(it.name,it.value)
        return True,cookie
    else:
        False,r.reason

"""
在xueqiu cookie过期后调用来重新初始化cookie
"""
def init_xueqiu_cookie(isinit=False):
    global xueqiu_cookie
    if not isinit:
        b,c = shared.fromRedis("XueqiuCookie")
        if b:
            xueqiu_cookie = c
            return c
    for i in range(10):
        b,c = xueqiuCookie()
        if b:
            xueqiu_cookie = c
            shared.toRedis(c,"XueqiuCookie")
            return c
        else:
            time.sleep(1)
    return ""

init_xueqiu_cookie()

def xueqiuJson(url,timeout=None):
    global xueqiu_cookie
    s = requests.session()
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate',
            'Cookie':xueqiu_cookie}
    if timeout is None:
        r = s.get(url,headers=headers)
    else:
        r = s.get(url,headers=headers,timeout=timeout)
    if r.status_code==200:
        return True,r.json()
    else:
        if r.status_code==400 and r.text.find('重新登录')>0:
            init_xueqiu_cookie(True)
            return xueqiuJson(url,timeout)
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
                            K.append((t,float(v[5])*100,float(v[1]),float(v[3]),float(v[4]),float(v[2])))
                    
                    return True,K[-n:]
                raise ValueError(str(r.text))
            else:
                raise ValueError(str(r.text))
        else:
            return False,r.reason
    except Exception as e:
        mylog.printe(e)
        return False,str(e)

#通过调用qqK5转换而来
def qqK15(code,n=32):
    b,K = qqK5(code,n=(n+1)*3)
    if b:
        if len(K)==(n+1)*3:
            k = []
            mod = K[0][0].minute%15
            if mod==5: #5-2,20-2,35-2,50-2
                bi = 0
            elif mod==10: #10-1,25-1,40-1,55-1
                bi = 2
            else: #15,30,45,00
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
            log.error("qqK15调用qqK5 '%s'返回的数量为%d,请求的数量为%d"%(code,len(K),n*3))
            return False,"qqK15调用qqK5 '%s'返回的数量为%d,请求的数量为%d"%(code,len(K),n*3)
    else:
        return b,K

#新浪资金流向,数据间隔2分钟
#返回数据结构
#[[date,larg,big,mid,tiny],...]
def getSinaFlow():
    try: 
        s = requests.session()
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9'}
        url = """https://stock.sina.com.cn/stock/api/jsonp.php/var%20_sh0000012020=/TouziService.getMinuteFlow?random=$rn"""
        r = s.get(url,headers=headers)
        if r.status_code==200:
            bi = r.text.find("=(\"")
            ei = r.text.find("\");")
            if bi>0 and ei>0 and ei>bi:
                a = r.text[bi+3:ei].split('|')
                flow = []
                for v in a:
                    vs = v.split(',')
                    if len(vs)==1: #year
                        year = vs[0]
                    elif len(vs)==5: #time,larg,big,mid,tiny
                        t = datetime.fromisoformat(year+' '+vs[0])
                        larg = float(vs[1])
                        big = float(vs[2])
                        mid = float(vs[3])
                        tiny = float(vs[4])
                        flow.append([t,larg,big,mid,tiny])
                    else:
                        raise ValueError(str(vs))
                return True,flow
            else:
                raise ValueError(str(r.text))
        else:
            return False,r.reason
    except Exception as e:
        mylog.printe(e)
        return False,str(e)

#将资金流向放入到redis中去
def sinaFlowRT():
    try:
        b,a = getSinaFlow()
        if b and len(a)>0:
            t=a[0][0]
            k = """flow_%d_%d"""%(t.month,t.day)
            shared.toRedis(a,k,ex=5*24*3600)
    except Exception as e:
        mylog.printe(e)

#返回当前的sinaflow
def sinaFlow(t=None):
    if t is None:
        t = datetime.today()
    name = "flow_%d_%d"%(t.month,t.day)
    b,a = shared.fromRedis(name)
    if b:
        F = []
        D = []
        for k in a:
            F.append(k[1:]) #(larg,big,mid,ting)
            D.append((k[0],))
        return K,D
    else:
        return None,None

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
                raise ValueError(str(r.text))
        else:
            return False,r.reason
    except Exception as e:
        mylog.printe(e)
        return False,str(e)

def sinaK15(code,n=32):
    return sinaK(code,15,n)
def sinaK5(code,n=96):
    return sinaK(code,5,n)
#将时间戳转换为日戳
def toDayTimestramp(ts):
    t = datetime.fromtimestamp(ts/1000000)
    return int(datetime(t.year,t.month,t.day).timestamp()*1000*1000)
#加速版本,使用全局变量
def defaultProgress(i):
    pass

_companys = None
def get_company_select():
    global _companys
    if _companys is None:
        #companys = stock.query("""select company_id,code,name,category,vmax,vmin from "company_select"")
        companys = stock.query("""select company_id,code,name,prefix from flow_em_category""")
        _companys = companys
    return _companys
def get_company_code2com():
    companys = get_company_select()
    code2com = {}
    for c in companys:
        code2com[c[1]] = c
    return code2com
def get_company_select_id2com():
    companys = get_company_select()
    id2com = {}
    for c in companys:
        id2com[c[0]] = c
    return id2com
def get_company_select_id2i():
    companys = get_company_select()
    id2i = {}
    for i in range(len(companys)):
        c = companys[i]
        id2i[c[0]] = i
    return id2i
#返回名称到分类的映射    
def get_category_name2category():
    categorys = stock.query("""select id,name from category""")
    name2category = {}
    for c in categorys:
        name2category[c[1]] = c
    return name2category
#上证选择    
def get_sh_selector():
    companys = get_company_select()
    s = np.zeros((len(companys),),dtype=np.dtype('bool'))
    for i in range(len(companys)):
        s[i] = companys[i][1][1]=='H'
    return s
def get_sz_selector():
    companys = get_company_select()
    s = np.zeros((len(companys),),dtype=np.dtype('bool'))
    for i in range(len(companys)):
        s[i] = companys[i][1][1]=='Z'
    return s
def get_cy_selector():
    companys = get_company_select()
    s = np.zeros((len(companys),),dtype=np.dtype('bool'))
    for i in range(len(companys)):
        s[i] = companys[i][1][1:5]=='Z300'
    return s
def get_kc_selector():
    companys = get_company_select()
    s = np.zeros((len(companys),),dtype=np.dtype('bool'))
    for i in range(len(companys)):
        s[i] = companys[i][1][1:5]=='Z688'
    return s
"""
返回某天的全部公司的总市值和价格
[
    [价格，市值]
    ...
]
"""
def get_volume_slice(date):
    companys = get_company_select()
    id2i = get_company_select_id2i()
    v = stock.query("""select id,volume,turnoverrate,close from kd_xueqiu where date='%s'"""%(date))
    V = np.array(v).reshape(-1,4)
    V[V[:,2]==0,2] = 1
    V[:,1] = V[:,1]/V[:,2]   
    result = np.ones((len(companys),2))
    for i in range(len(V)):
        K = V[i]
        if K[0] in id2i:
            j = id2i[K[0]]
            result[j,0] = K[3] #price
            result[j,1] = K[1] #tv

    return result
"""
返回分类的选择器表
返回如下结构
{
    "category name":r #分类器选择向量
}
"""
def get_category_selector():
    companys = get_company_select()
    result = {}
    cc = np.empty(len(companys),dtype=np.dtype('O'))
    for i in range(len(companys)):
        c = companys[i]
        if c[3] is not None:
            if c[3] not in result:
                result[c[3]] = np.zeros((len(companys),),dtype=np.dtype('bool'))
            cc[i] = c[3]
    for k in result:
        result[k][cc==k] = True
    return result
"""
返回company_select中公司的全部60分钟数据
"""
_K60 = {240:None,60:None,30:None,15:None}
_D60 = {240:None,60:None,30:None,15:None}
_N60 = {240:None,60:None,30:None,15:None}
def get_period_k(period):
    global _K60,_D60,_N60
    
    b,seqs = shared.fromRedis('k%d_sequence'%period)
    companys = get_company_select()
    C = len(companys)
    if b:
        if _D60[period] is None:
            L = 257
            _D60[period] = [None]*L
            _K60[period] = np.empty((len(companys),L)) #company_id,close
            _N60[period] = 0
            for i in range(len(seqs)-240,len(seqs)):
                if i>=0:
                    ts = seqs[i]
                    b,p = shared.numpyFromRedis("k%d%d"%(period,ts))
                    if b:
                        _K60[period][:,_N60[period]] = p
                        _D60[period][_N60[period]] = (datetime.fromtimestamp(ts),ts)
                        _N60[period]+=1
        else:
            lastts = _D60[period][_N60[period]-1][1]
            ba = False
            for i in range(len(seqs)):
                ts = seqs[i]
                if ba:
                    b,p = shared.numpyFromRedis("k%d%d"%(period,ts))
                    if b:
                        _K60[period][:,_N60[period]] = p
                        _D60[period][_N60[period]] = (datetime.fromtimestamp(ts),ts)
                        _N60[period]+=1
                elif ts==lastts:
                    ba = True
        #将最新的帧数据刷新到_K60中去
        b,p = shared.numpyFromRedis("k%d%d"%(period,seqs[-1]))
        if b:
            _K60[period][:,_N60[period]-1] = p
    if _K60[period] is not None:
        bi = 0
        return _K60[period][:,bi:_N60[period]],_D60[period][bi:_N60[period]]
    else:
        return None,None

#产生一个period时间序列
def build_timestamp_sequence(d,period):
    seqs = []
    bi = datetime(year=d.year,month=d.month,day=d.day,hour=9,minute=30)
    ei = datetime(year=d.year,month=d.month,day=d.day,hour=11,minute=30)
    delta = timedelta(minutes=period)
    t = bi+delta
    while t<=ei:
        seqs.append(t.timestamp())
        t += delta
    bi = datetime(year=d.year,month=d.month,day=d.day,hour=13,minute=0)
    ei = datetime(year=d.year,month=d.month,day=d.day,hour=15,minute=0)
    delta = timedelta(minutes=period)
    t = bi+delta
    while t<=ei:
        seqs.append(t.timestamp())
        t += delta
    return seqs

def next_period_timestamp(d,period):
    if period==240:
        return datetime(year=d.year,month=d.month,day=d.day).timestamp()
    else:
        bi = datetime(year=d.year,month=d.month,day=d.day,hour=9,minute=30)
        ei = datetime(year=d.year,month=d.month,day=d.day,hour=15,minute=0)
        delta = timedelta(minutes=period)
        t = bi+delta
        while t<=ei:
            if t>=d:
                return t.timestamp()
            t += delta
    return None

def period_ex(period):
    if period==60:
        return 3*30*24*3600 #3个月
    elif period==30:
        return int(1.5*30*24*3600) #1.5个月
    else:
        return 30*24*3600 #1个月
"""
向k60中增加数据
"""        
def update_period_plane(t,plane,periods):
    for period in periods:
        ts = next_period_timestamp(t,period)
        if ts is None:
            continue
        b,_ = shared.numpyFromRedis("k%d%d"%(period,ts))
        if not b:
            b,seqs = shared.fromRedis('k%d_sequence'%period)
            if b:
                seqs.append(ts)
                for i in range(0,len(seqs)-240,1):
                    shared.delKey("k%d%d"%(period,seqs[i]))
                seqs = seqs[-240:] #保留240个数据点
                shared.toRedis(seqs,'k%d_sequence'%period)            
            else:
                continue
        shared.numpyToRedis(plane[:,0,0],"k%d%d"%(period,ts),ex=period_ex(period)) #3个月

#处理plane数据，使其不存在0,如果有0就用左边或者右边的数据替代
def nozero_plane(plane):
    N = plane.shape[1]
    for i in range(N):
        if i>0: #正向
            plane[plane[:,i]==0,i] = plane[plane[:,i]==0,i-1]
        j = N-1-i
        if j<N-1: #反向
            plane[plane[:,j]==0,j] = plane[plane[:,j]==0,j+1]
"""
每天使用xueqiu数据覆盖实时收集到的数据,确保数据的准确一致
函数在每天下载完数据后调用
"""
def update_today_period(periods_args):
    dd = stock.query("""select date from kd_xueqiu where id=8828 order by date desc limit 1""")
    companys = get_company_select()
    t = dd[0][0]
    
    if t==date.today():
        periods = []
        isdd = False
        for p in periods_args:
            if p<240:
                periods.append(p)
            else:
                isdd = True
        if isdd: #使用kd_xueqiu数据来产生日线级别的数据
            period=240
            S = ""
            for c in companys:
                if c[1][0]!='B':
                    S += '%d,'%c[0]
            p1 = stock.query("select id,date,close from kd_xueqiu where date='%02d-%02d-%02d' and id in (%s)"%(t.year,t.month,t.day,S[:-1]))
            p2 = stock.query("select id,date,close from kd_em where date='%02d-%02d-%02d'"%(t.year,t.month,t.day))
            p = p1+p2
            b,seqs = shared.fromRedis('k%d_sequence'%period)
            if not b:
                rebuild_period_sequence(period)
                return
            for i in range(96): #删除今天的rt时间戳
                tt = datetime.fromtimestamp(seqs[-1])
                if tt.day==t.day and tt.month==t.month and tt.year==t.year:
                    del seqs[-1]
                else:
                    break
            seqs.append(detetimestamp(t))
            id2i = {}
            for i in range(len(companys)):
                id2i[companys[i][0]] = i

            plane = np.zeros((len(companys),))
            for v in p:
                cid = v[0]
                ts = detetimestamp(v[1])
                if cid in id2i:
                    plane[id2i[cid]] = v[2]
            shared.numpyToRedis(plane[:],"k%d%d"%(period,seqs[-1]),ex=period_ex(period))
            shared.toRedis(seqs,'k%d_sequence'%period)
        if len(periods)>0:
            S = ""
            p1 = []
            for c in companys:
                if c[1][0]!='B':
                    p1 += stock.query("select id,timestamp,close from k5_xueqiu where id=%d and timestamp>'%02d-%02d-%02d'"%(c[0],t.year,t.month,t.day))
            p2 = stock.query("select id,timestamp,close from k5_em where timestamp>'%02d-%02d-%02d'"%(t.year,t.month,t.day))
            p = p1+list(p2)
            for period in periods:
                b,seqs = shared.fromRedis('k%d_sequence'%period)
                if not b:
                    rebuild_period_sequence(period)
                    return
                for i in range(96): #删除今天的rt时间戳
                    tt = datetime.fromtimestamp(seqs[-1])
                    if tt.day==t.day and tt.month==t.month:
                        del seqs[-1]
                    else:
                        break
                seqs_today = build_timestamp_sequence(t,period)
                timestamp2i = {}
                for i in range(len(seqs_today)):
                    timestamp2i[seqs_today[i]] = i
                    seqs.append(seqs_today[i])
                id2i = {} 
                for i in range(len(companys)):
                    id2i[companys[i][0]] = i

                plane = np.zeros((len(companys),len(seqs_today)))
                for v in p:
                    cid = v[0]
                    ts = v[1].timestamp()
                    if ts in timestamp2i and cid in id2i:
                        plane[id2i[cid],timestamp2i[ts]] = v[2]
                nozero_plane(plane)
                for i in range(len(seqs_today)):
                    shared.numpyToRedis(plane[:,i],"k%d%d"%(period,seqs_today[i]),ex=period_ex(period))
                shared.toRedis(seqs,'k%d_sequence'%period)
    else:
        print("今天的数据还没有更新完成，不能k%d_sequence数据"%periods_args)

def clear_period_sequence(period):
    b,seqs = shared.fromRedis('k%d_sequence'%period)
    if b:
        for ts in seqs:
            shared.delKey("k%d%d"%(period,ts))
        shared.delKey('k%d_sequence'%period)

def detetimestamp(d):
    return int(datetime(year=d.year,month=d.month,day=d.day).timestamp())
"""
删除以前的k60 sequence数据，然后从数据库重新加载
period = 60,30,15
"""        
def rebuild_period_sequence(period):
    #删除以前的数据
    companys = get_company_select()
    b,seqs = shared.fromRedis('k%d_sequence'%period)
    if b:
        bb,f = shared.numpyFromRedis("k%d%d"%(period,seqs[-1]))
        dd = stock.query("""select date from kd_xueqiu where id=8828 order by date desc limit 1""")
        t = datetime.fromtimestamp(seqs[-1])
        lastdate = date(year=t.year,month=t.month,day=t.day)
        if bb and len(f)==len(companys) and dd[0][0]<=lastdate:
            return #已经有完整的加载数据了不需要重新加载
    if b:
        for ts in seqs:
            shared.delKey("k%d%d"%(period,ts))
    print("rebuild_k%d_sequence..."%period)
    if period==240: #使用kd_xueqiu数据来产生日线级别的数据
        dd = stock.query("""select date from kd_xueqiu where id=8828 order by date desc limit 240""")
        timestamp2i = {}
        seqs = []
        for i in range(len(dd)-1,-1,-1):
            d = dd[i][0]
            seqs.append(detetimestamp(d))
        for i in range(len(seqs)):
            timestamp2i[seqs[i]]=i
        plane = np.zeros((len(companys),240)) #close
        bits = stock.dateString(dd[-1][0])
        for i in range(len(companys)):
            c = companys[i] #0 company_id,1 code,2 name,3 name
            p = stock.query("""select date,close from %s where id=%d and date>='%s'"""%('kd_em' if c[1][0]=='B' else 'kd_xueqiu',c[0],bits)) #B开头的存放在kd_em中分类和概念
            for k in p:
                ts = detetimestamp(k[0])
                if ts in timestamp2i:
                    plane[i,timestamp2i[ts]] = k[1]        
    else:
        dd = stock.query("""select date from kd_xueqiu where id=8828 order by date desc limit 60""")
        timestamp2i = {}
        seqs = []
        for i in range(-1,-len(dd)-1,-1):
            t = dd[i][0]
            for v in build_timestamp_sequence(t,period):
                seqs.append(v)
        seqs = seqs[-240:]
        for i in range(len(seqs)):
            timestamp2i[int(seqs[i])]=i
        plane = np.zeros((len(companys),240)) #close
        bits = stock.dateString(datetime(year=dd[-1][0].year,month=dd[-1][0].month,day=dd[-1][0].day))
        for i in range(len(companys)):
            c = companys[i]
            p = stock.query("""select timestamp,close from %s where id=%d and timestamp>'%s'"""%('k5_em' if c[1][0]=='B' else 'k5_xueqiu',c[0],bits))
            for k in p:
                ts = int(k[0].timestamp())
                if ts in timestamp2i:
                    plane[i,timestamp2i[ts]] = k[1]
    nozero_plane(plane)
    for i in range(240):
        try:
            shared.numpyToRedis(plane[:,i],"k%d%d"%(period,seqs[i]),ex=period_ex(period))
        except Exception as e:
           mylog.printe(e)
    shared.toRedis(seqs,'k%d_sequence'%period)
    print("rebuild_%d_sequence done"%period)

"""
返回company_select中公司的全部分时数据
companys company_select表的返回
step     间隔多少取一个数据
N        返回表的长度，丢弃较早的数据,0表示全部数据
progress 进度回调
返回K = [[[0 id,1 timestamp,2 volume,3 current,4 yesterday_close,5 today_open]
       ....
     len(companys)],]
     shape = (len(companys),len(D),6)
D = [(datetime,),....]
没有数据返回None,None
"""
_K = None
_D = None
_N = None
def getRT(step=1,N=100,progress=defaultProgress):
    global _K,_D,_N
    b,seqs = shared.fromRedis('runtime_sequence')
    companys = get_company_select()
    C = len(companys)
    progress(0)
    if b:
        if _D is None:
            L = 60*4*3*7
            _D = [None]*L
            _K = np.empty((len(companys),L,6))
            _N = 0
            for ts in seqs:
                b,p = shared.numpyFromRedis("rt%d"%ts)
                if b:
                    _K[:,_N,:] = p
                    _D[_N] = (datetime.fromtimestamp(ts/1000000),ts)
                    _N+=1
        else:
            lastts = _D[_N-1][1]
            ba = False
            for ts in seqs:
                if ba:
                    b,p = shared.numpyFromRedis("rt%d"%ts)
                    if b:
                        _K[:,_N,:] = p
                        _D[_N] = (datetime.fromtimestamp(ts/1000000),ts)
                        _N+=1
                elif ts==lastts:
                    ba = True
    if _K is not None:
        if step==1:
            bi = _N-N
            if bi<0:
                bi = 0
            return _K[:,bi:_N,:],_D[bi:_N]
        else:
            x = np.arange(0,_N,step)
            K = np.take(_K,x,axis=1)
            D = np.take(_D,x)
            if x[-1]!=_N-1:
                K[:,-1,:] = _K[:,_N-1,:]
            return K[:,-N:,:],D[-N:]
    else:
        return None,None

#遍历全部的数据帧
#cb是回调函数，cb(timestamp,plane)
def foreachRT(cb):
    b,seqs = shared.fromRedis('runtime_sequence')
    if b:
        for ts in seqs:
            b,p = shared.numpyFromRedis("rt%d"%ts)
            if b:
                cb(ts,p)
#返回最后一帧数据,返回plane,timestamp
def lastRT(i=-1):
    b,seqs = shared.fromRedis('runtime_sequence')
    if b:
        ts = seqs[i]
        b,p = shared.numpyFromRedis("rt%d"%ts)
        if b:
            t = datetime.fromtimestamp(ts/1000000)
            return p,t
    return None,None
#返回最后一次更新分时数据的时间
def getLastUpdateTimestamp():
    return shared.fromRedis('runtime_update')
_companyLastK = {}
#返回一个公司最近的k,d数据
def getCompanyLastK(idd):
    global _companyLastK
    if idd in _companyLastK:
        return _companyLastK[idd]
    k = stock.query("""select date,volume,open,high,low,close from kd_xueqiu where id=%d order by date desc limit 1"""%(idd))
    if len(k)>0:
        _companyLastK[idd] = ((k[0][1],k[0][2],k[0][3],k[0][4],k[0][5]),k[0][0])
    else:
        _companyLastK[idd] = ((1,1,1,1,1),(datetime.today(),))
    return _companyLastK[idd]
#检查数据帧看看current是不是为0
def checkFrame(plane):
    b = False
    for i in range(len(plane)):
        p = plane[i]
        if p[2]<=0 or p[3]<=0 or p[4]<=0:
            k,_ = getCompanyLastK(int(p[0])) #取指定公司的最后一个k线数据
            plane[i,2:] = [k[0],k[4],k[4],k[4]]
            b = True
    return True
#当company_select改变时，重新对过往的实时数据进行调整，调整完后和company_select当前的状态保持一致
def rebuild_runtime_sequence(idds,seqs):
    plane = np.zeros((len(idds),6),dtype=float)
    mapit = None #假设过往数据，公司的数量一样多并且顺序相同
    for i in range(len(idds)):
        plane[i] = idds[i]
    for n in seqs:
        b,f = shared.numpyFromRedis("rt%d"%n)
        if b:
            #如果mapit还没有生成，这里构造mapit
            if mapit is None:
                mapit = []
                id2j = {}
                for i in range(len(f)):
                    id2j[int(f[i,0])] = i
                for i in range(len(idds)):
                    idd = idds[i]
                    if idd in id2j:
                        mapit.append(id2j[idd])
                    else:
                        mapit.append(-1)
            for i in range(len(idds)):
                j = mapit[i]
                if j>=0:
                    plane[i,1:] = f[j,1:]
                else:
                    k,_ = getCompanyLastK(int(idds[i]))
                    plane[i,1:] = [0,k[0],k[4],k[4],k[4]]
            shared.numpyToRedis(plane,"rt%d"%n,ex=4*24*3600)


#清除全部实时数据
def clearAllRT():
    b,seqs = shared.fromRedis('runtime_sequence')
    if b:
        for ts in seqs:
            shared.delKey("rt%d"%ts)
        shared.delKey('runtime_sequence')
        shared.delKey('runtime_update')
#更新全部数据
def updateAllRT(ThreadCount=config.updateAllRT_thread_count):
    b,_ = shared.fromRedis('runtime_update')
    if b:
        print('更新程序已经在运行了')
        return 'alrady'
    companys = stock.query("""select company_id,code,name,category from company_select""")
    coms = []
    idds = []
    for c in companys:
        idds.append(c[0])
        coms.append(c[1])
    t = datetime.today()
    print('开始实时更新全部数据...')
    b,seqs = shared.fromRedis('runtime_sequence')
    if not b:
        seqs = []
    lastUpdateFlow = -1
    #如果company_select中的公司数量改变了确保过往的临时数据也做相应的改变
    try:
        if len(seqs)>0:
            b,f = shared.numpyFromRedis("rt%d"%seqs[-1])
            if b and len(f)!=len(idds): #数量不对需要对过往数据做重新修正
                rebuild_runtime_sequence(idds,seqs)
        rebuild_period_sequence(240)    #'d'            
        rebuild_period_sequence(60)
        rebuild_period_sequence(30)
        rebuild_period_sequence(15)
    except Exception as e:
        mylog.printe(e)
    while t.hour>=6 and t.hour<15:
        try:
            if stock.isTransTime():
                if t.minute!=lastUpdateFlow: #每1分钟更新一次
                    lastUpdateFlow = t.minute
                    sinaFlowRT()
                    print("sinaFlowRT %s"%str(t))
                    plane = emflowRT2()
                    if plane is not None:
                        update_period_plane(t,plane,[240,60,30,15])
                    print("emflowRT %s"%str(t))
                shared.toRedis(datetime.today(),'runtime_update',ex=60)                
            dt = 20-(datetime.today()-t).seconds #20秒更新一次
            if dt>0:
                time.sleep(dt)
            t = datetime.today()
        except Exception as e:
            mylog.printe(e)
    return 'done'

#(0 code,1 timesramp,2 volume,3 open,4 high,5 low,6 close)
def appendRedisRT(code,timestamp,volume,open1,high,low,close1,yesterday_close,today_open):
    name = "%s_RT"%code
    b,rt = shared.fromRedis(name)
    if not b or rt['v']!=1:
        rt = {'kk':{},'k':[],'r':[],'l':0,'v':1}
    rt['r'].append((timestamp,volume,open1,high,low,close1,yesterday_close,today_open))
    rt['r'] = rt['r'][-180:]
    t = next_k_timestamp(timestamp)
    if t is not None:
        ts = "%02d:%02d"%(t.hour,t.minute)
        if ts not in rt['kk']:
            if volume>0 and rt['l']>0:
                rt['kk'][ts] = [t,volume-rt['l'],open1,high,low,close1,0]
            else:
                rt['kk'][ts] = [t,0,open1,high,low,close1,0]
            rt['k'].append(rt['kk'][ts])
            rt['kk'][ts][6] = len(rt['k'])-1 #将索引放入到5中，便于查找
        else:
            k = rt['kk'][ts]
            if volume>0:
                k[1] += volume-rt['l']
                rt['l'] = volume
            k[3] = max(k[3],high)
            k[4] = min(k[4],low)
            k[5] = close1
            
    shared.toRedis(rt,name,ex=8*3600)

#返回
def K2(code,n=48):
    cacheName = "k5_%s"%(code.lower())
    b,cache = shared.fromRedis(cacheName)
    if b:
        rtname = "%s_RT"%code
        b1,rt = shared.fromRedis(rtname)
        if b1:
            k_ = cache['k']
            d_ = cache['date']
            if len(k_)<n:
                return K(code,5,n)
            dd = cache['date'][-1][0]
            nd = next_k_timestamp(dd)
            if nd is not None:
                ts = "%02d:%02d"%(nd.hour,nd.minute)
                if ts in rt['kk']:
                    bi = rt['kk'][ts][6]
                    k = rt['k']
                    ad = []
                    ak = []
                    for i in range(bi,len(k)):
                        p = k[i]
                        ak.append(p[1:6])
                        ad.append((p[0],))
                        #if True: #是否连续
                        #    return K(code,5,n)
                    if len(ad)>0:
                        return True,np.vstack((k_,ak))[-n:],(d_+ad)[-n:]
                    else:
                        return True,k_,d_
    return K(code,5,n)
#读取实时k数据
#返回b,(timestamp,volume,open,high,low,close) 5k
def readRedisRT(code):
    pass
#雪球实时https://stock.xueqiu.com/v5/stock/realtime/quotec.json?symbol=SH000001,SZ399001,SZ399006&_=1583718246079
#codes = [code,...]
#返回b,[(timestamp,volume,open,high,low,close),...]
"""
{
    "data": [
        {
            "symbol": "SZ002418",
            "current": 2.68,
            "percent": 0.75,
            "chg": 0.02,
            "timestamp": 1583719068000,
            "volume": 9168078,
            "amount": 24406681,
            "market_capital": 3045552000,
            "float_market_capital": 2688409910,
            "turnover_rate": 0.91,
            "amplitude": 4.14,
            "open": 2.61,
            "last_close": 2.66,
            "high": 2.71,
            "low": 2.6,
            "avg_price": 2.662,
            "trade_volume": 0,
            "side": -1,
            "is_trade": false,
            "level": 1,
            "trade_session": null,
            "trade_type": null,
            "current_year_percent": -6.29,
            "trade_unique_id": "9168078",
            "type": 11,
            "bid_appl_seq_num": null,
            "offer_appl_seq_num": null
        },
        ....]
}
"""
def xueqiuRT(codes,result=None):
    timestramp = math.floor(time.time()*1000)
    cs = ""
    code2i = {}
    inx = 0
    for c in codes:
        cs += "%s,"%(c.upper())
        code2i[c.lower()] = inx
        inx +=1
    uri = "https://stock.xueqiu.com/v5/stock/realtime/quotec.json?symbol=%s&_=%d"%(cs[:-1],timestramp)
    try:
        b,js = xueqiuJson(uri,timeout=3)
        if b:
            if 'data' in js:
                data = js['data']
                for i in range(len(data)):
                    d = data[i]
                    try:
                        if 'current' in d and d['current'] is not None:
                            current = float(d['current'])
                        else:
                            return False
                        if d['volume'] is not None:
                            vol = float(d['volume'])
                        else:
                            vol = 0
                        if d['open'] is not None:
                            today_open = float(d['open'])
                        else:
                            today_open = 0
                        if d['last_close'] is not None:
                            yesterday_close = float(d['last_close'])                            
                        else:
                            yesterday_close = 0
                        if result is None:                  
                            appendRedisRT(d['symbol'],datetime.fromtimestamp(d['timestamp']/1000),vol,current,current,current,current,yesterday_close,today_open)
                        elif current>0:
                            code = d['symbol'].lower()
                            if code in code2i:
                                result[code2i[code]] = [d['timestamp']/1000,vol,current,yesterday_close,today_open]
                            else:
                                result[i] = [d['timestamp']/1000,vol,current,yesterday_close,today_open]
                    except Exception as e:
                        mylog.printe(e)
                        return False
                return True
        log.error('xueqiuRT:'+str(js))
        return False
    except Exception as e:
        mylog.printe(e)
        return False    
    return False        
#http://hq.sinajs.cn/rn=oablq&list=sh601872,sh601696,...
#var hq_str_sh600278="东方创业,11.680,11.170,11.680,11.680,11.680,11.670,11.680,1740300,20326704.000,14800,11.670,200,11.660,800,11.610,140100,11.560,50800,11.550,54100,11.680,300,11.690,23700,11.700,1200,11.710,1400,11.720,2020-03-09,09:29:35,00,";
#var hq_str_code="0 name,1 today_open,2 last_close,3 open,4 high,5 low,6 close,7 current,8 成交量,9 成交额,(v,p),...10个,timestamp"
def sinaRT(codes,result=None):
    cs = ""
    inx = 0
    code2i = {}
    for c in codes:
        cs += "%s,"%(c.lower())    
        code2i[c.lower()] = inx
        inx += 1
    uri = "http://hq.sinajs.cn/rn=%s&list=%s"%(str(uuid.uuid4())[:5],cs[:-1])
    try:
        s = requests.session()
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9'}
        r = s.get(uri,headers=headers,timeout=3)
        if r.status_code==200:
            bi = 0
            ei = 0
            i = 0
            while ei!=-1:
                ei = r.text.find('\n',bi)
                ln = r.text[bi:ei]
                if len(ln)>16 and ln[:11]=='var hq_str_':
                    code = ln[11:11+8].lower()
                    bii = ln.find('="')
                    eii = ln.find('";')
                    if bii!=-1 and eii!=-1:
                        code = ln[11:19].upper()
                        a = ln[bii+2:eii].split(',')
                        if len(a)>31:
                            timestamp = datetime.fromisoformat(a[30]+' '+a[31])
                            open1=float(a[3])
                            high = float(a[4])
                            low = float(a[5])
                            close1=float(a[6])
                            today_open = float(a[1])
                            yesterday_close = float(a[2])
                            lastp = 0
                            for j in range(10,30,2):
                                p = float(a[j+1])
                                if p>1:
                                    high = max(high,p)
                                    low = min(low,p)
                                    lastp = p
                            if open1==0:
                                open1 = float(a[11])
                            if close1==0:
                                close1 = lastp
                            if result is None:
                                appendRedisRT(code,timestamp,float(a[8]),open1,high,low,close1,yesterday_close,today_open)
                            elif open1>0 and high>0 and low>0 and close1>0:
                                if code in code2i:
                                    result[code2i[code]] = [timestamp.timestamp(),float(a[8]),open1,yesterday_close,today_open]
                                else:
                                    result[i] = [timestamp.timestamp(),float(a[8]),open1,yesterday_close,today_open]
                            i+=1
                bi = ei+1
            return True
        else:
            log.error('sinaRT:'+str(r.reason))
            return False
    except Exception as e:
        mylog.printe(e)
        return False
    return False
#http://qt.gtimg.cn/q=sh601872,sh600370,sh600312,sh603559,sh600302,sh600252,sh600798&r=573645421
#v_sh600302="1~标准股份~600302~5.11~4.80~5.20~89408~47563~41845~5.10~99~5.09~17~5.08~104~5.07~30~5.06~5~5.11~769~5.13~888~5.15~966~5.16~500~5.17~508~~20200309093940~0.31~6.46~5.20~4.82~5.11/89408/45641325~89408~4564~2.58~-165.44~~5.20~4.82~7.92~17.68~17.68~1.52~5.28~4.32~53.32~-3376~5.10~-18.29~62.32~~~1.14~4564.13~0.00~0~ ~GP-A~1.39~~0.00~-0.92~-0.66";
def qqRT(codes,result=None):
    cs = ""
    inx = 0
    code2i = {}
    for c in codes:
        cs += "%s,"%(c.lower())    
        code2i[c.lower()] = inx
        inx += 1
    rn = str(math.floor(time.time()*1000))[1:10]
    uri = "http://qt.gtimg.cn/q=%s&r=%s"%(cs[:-1],rn)
    try:
        s = requests.session()
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9'}
        r = s.get(uri,headers=headers,timeout=3)
        if r.status_code==200:
            bi = 0
            ei = 0
            i = 0
            while ei!=-1:
                ei = r.text.find('\n',bi)
                ln = r.text[bi:ei]
                if len(ln)>16 and ln[:2]=='v_':
                    a = ln.split('~')
                    if len(a)==67:
                        code = a[0][2:10].lower()
                        ts = a[30] #20200309093940
                        timestamp = datetime(int(ts[:4]),int(ts[4:6]),int(ts[6:8]),int(ts[8:10]),int(ts[10:12]),int(ts[12:]))
                        vol = float(a[6])*100
                        yesterday_close = float(a[4])
                        today_open = float(a[5])
                        open1 = today_open
                        for i in range(10):
                            c = float(a[2*i+9])
                            if i==0:
                                close1 = c
                                high = c
                                low = c
                            if c>0:
                                high = max(high,c)
                                low = min(low,c)
                                open1 = c
                        if result is None:
                            appendRedisRT(code,timestamp,vol,open1,high,low,close1,yesterday_close,today_open)
                        elif vol>0 and open1>0 and high>0 and low>0 and close1>0:
                            if code in code2i:
                                result[code2i[code]] = [timestamp.timestamp(),vol,open1,yesterday_close,today_open]
                            else:
                                result[i] = [timestamp.timestamp(),vol,open1,yesterday_close,today_open]
                        i+=1
                bi = ei+1
            return True
        else:
            log.error('qqRT:'+str(r.reason))
            return False
    except Exception as e:
        mylog.printe(e)
        return False
    return False

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
            return b,dd
    except Exception as e:
        mylog.printe(e)
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
    log.warning("==============stockK15Service=============")
    for it in stockK15Service:
        log.warning("%s error:%d success:%d avg:%fms"%(it['name'],it['error'],it['success'],1000*it['avg']))
        if 'errmsg' in it:
            log.warning(str(it['errmsg']))
            it['errmsg'].clear()
    log.warning("==============stockK5Service=============")
    for it in stockK5Service:
        log.warning("%s error:%d success:%d avg:%fms"%(it['name'],it['error'],it['success'],1000*it['avg']))
        if 'errmsg' in it:
            log.warning(str(it['errmsg']))        
            it['errmsg'].clear()

#下载K数据，返回True/False,[(timesramp,volume,open,high,low,close)...],source
def getK(code,period,n,provider=None):
    service = None
    if period==5:
        service = stockK5Service
    elif period==15:
        service = stockK15Service
    CODE = code.upper()
    if CODE=='SZ399001' or CODE=='SH000001' or CODE=='SZ399006' or CODE[0]=='B': #主要指数使用xueqiu数据，不同来源的数据成交量有差异
        if period == 15:
            provider = u'雪球k15'
        else:
            provider = u'雪球k5'
    if service is not None:
        for i in range(10):
            if provider is None:
                current = random.randint(0,len(service)-1)
            else:
                for i in range(len(service)):
                    if service[i]['name']==provider:
                        current = i
                        break
            t0 = time.time()
            b,d = service[current]['cb'](code,n)

            if b:
                service[current]['success'] +=1
                service[current]['total'] += time.time()-t0
                service[current]['avg'] = service[current]['total']/service[current]['success']
                return b,d,service[current]['name']
            else:
                service[current]['error'] += 1
                if not 'errmsg' in service[current]:
                    service[current]['errmsg'] = []
                service[current]['errmsg'].append(d)
    logServiceState()
    return False,0,0

#返回下一个正确的时间k日期,输入时间t必须是一个正确的时间戳
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
    for i in range(len(k0)):
        if abs(k0[i]/k1[i]-1)>0.05:
            return False
    return True

#产生一个日期表便于查找
k5date = []
for i in [9,10,11,13,14,15]:
    if i in [10,14]:
        for m in range(0,60,5):
            k5date.append((i,m))
    elif i==9:
        for m in range(35,60,5):
            k5date.append((i,m))
    elif i==11:
        for m in range(0,35,5):
            k5date.append((i,m))
    elif i==13:
        for m in range(5,60,5):
            k5date.append((i,m))
    else:
        k5date.append((i,0))
k15date = []
for i in [9,10,11,13,14,15]:
    if i in [10,14]:
        for m in range(0,60,15):
            k15date.append((i,m))
    elif i==9:
        for m in range(45,60,15):
            k15date.append((i,m))
    elif i==11:
        for m in range(0,35,15):
            k15date.append((i,m))
    elif i==13:
        for m in range(15,60,15):
            k15date.append((i,m))
    else:
        k15date.append((i,0))

#计算从t到当前时间存在多少个k点
def from2now(t,period):
    n = 0
    m = k15date if period==15 else k5date
    today = datetime.today()
    if today.day!=t.day:
        hour = t.hour
        minute = t.minute
        for d in m:
            if d[0]>hour or (d[0]==hour and d[1]>=minute):
                n += 1
        hour = 9
        minute = 30            
        for d in m:
            if (d[0]>hour or (d[0]==hour and d[1]>minute)) and (today.hour>d[0] or (today.hour==d[0] and today.minute>=d[1])):
                n += 1
    else:
        hour = t.hour
        minute = t.minute
        for d in m:
            if (d[0]>hour or (d[0]==hour and d[1]>minute)) and (today.hour>d[0] or (today.hour==d[0] and today.minute>=d[1])):
                n += 1
    return n

def next_k_date(period):
    if period==5:
        m = k5date
    else:
        m = k15date
    today = datetime.today()
    for d in m:
        if today.hour<d[0] or (today.hour==d[0] and today.minute<d[1]):
            return (datetime(today.year,today.month,today.day,d[0],d[1])-today).seconds
    return 0

#下一个k时间戳
def next_k_timestamp(t,period=5):
    if period==5:
        m = k5date
    else:
        m = k15date
    for i in range(len(m)):
        d = m[i]
        if t.hour<d[0] or t.hour==d[0] and t.minute<d[1]:
            return datetime(t.year,t.month,t.day,d[0],d[1])
    return None
def prev_k_timestamp(t,period=5):
    if period==5:
        m = k5date
    else:
        m = k15date
    for i in range(len(m)):
        d = m[i]
        if t.hour<d[0] or t.hour==d[0] and t.minute<d[1]:
            if i > 0:
                return datetime(t.year,t.month,t.day,m[i-1][0],m[i-1][1])
            else:
                break
    return None
#如果是在开盘状态则15分钟更新一次数据
def nextdt15():
    t = datetime.today()
    if (t.hour==11 and t.minute>=30) or t.hour==12:#中午休息需要跳过
        return (datetime(t.year,t.month,t.day,13,15,0)-t).seconds+15*60
    return (15-t.minute%15)*60-t.second

def datetimeString(t):
    return '%s-%s-%s %s:%s:%s'%(t.year,t.month,t.day,t.hour,t.minute,t.second)
#将数据和数据库中的对应数据进行比较
def checkK(code,period,k,d,base,n):
    today = date.today()
    if d[0][0].day!=today.day: #存在不在一天的数据就可以进行检查
        c,K,D = stock.loadKline(code,period,after=datetimeString(d[0][0]))
        log.warning("checkK %s,%s,%s,%d"%(code,period,base,n))        
        for i in range(len(k)):
            if d[i][0]!=today.day and i<len(K) and not isEqK(k[i],K[i]):
                log.warning("%d\t%s\t%s"%(i,str(d[i][0]),str(k[i])))
                log.warning("%d\t%s\t%s"%(i,str(D[i][0]),str(K[i])))
                break
#返回指定代码的k线数据
# True , np.array((timesramp,volume,open,high,low,close),...),[(timesramp,)...] 保持和loadKline相同的数据结构
# False, "Error infomation"
#缓存区保持两天的数据量
def K(code,period,n):
    base = None
    cacheName = "k%s_%s"%(str(period).lower(),code.lower())
    #cache = {'k':np.array((volume,open,high,low,close),...),'date':[(timesramp,)...],'base':} base是最初的数据来源
    b,cache = shared.fromRedis(cacheName)
    if b and 'ver' in cache and cache['ver']==3:
        if b and len(cache['k'])>=n and nextKDate(cache['date'][-1][0],period)>datetime.today(): #存在缓存并且没有新的数据直接返回
            return b,cache['k'][-n:],cache['date'][-n:]
    else:
        b = False
        cache = None
    
    if b: #如果有数据那么仅仅下载最新数据和部分校验用数据
        base = cache['base']
        #还需要下载多少数据
        t = cache['date'][-1][0]
        dn = from2now(t,period)
        if dn==0:
            return b,cache['k'][-n:],cache['date'][-n:]
    elif n<15*16/period:
        dn = int(15*16/period)
    else:
        dn = n
    #fixbug: 非雪球数据etf有问题，这里暂时强行改成雪球数据
    if period==5:
        base = '雪球k5'
    else:    
        base = '雪球k15'
    a,k,s = getK(code,period,dn,provider=base)
    K = []
    if a and b:
        #校验重叠区域数据,合并数据
        oldK = cache['k']
        d = cache['date']
        bi = -1
        for i in range(len(k)-1,-1,-1): #找到重叠部分
            if k[i][0]==d[-1][0]:
                bi = i
                break
        #如果有接缝，校验接缝处的数据
        if bi>=0 and not isEqK(oldK[-1,1:],k[bi][2:]): #不做成交量校验了
            log.error("K '%s' %s base='%s' 和 '%s'存在%d处存在较大差异"%(code,str(period),base,s,bi))
            log.error("oldK=%s,%s"%(str(d[-1]),str(oldK[-1])))
            log.error("k[bi]=%s"%(str(k[bi])))

        for i in range(bi+1,len(k)):
            v = k[i]
            K.append((v[1],v[2],v[3],v[4],v[5]))
            d.append((v[0],))
        if len(K)>0:
            k = np.vstack((oldK,K))
        else:
            return True,oldK,d
    elif a:
        base = s
        d = []
        for v in k:
            K.append((v[1],v[2],v[3],v[4],v[5]))
            d.append((v[0],))
        k = np.array(K)
    else:
        log.error("'%s' %s %s 下载时出错"%(code,str(period),base))
        return False,0,0
    
    #太长就进行截取,保留5天的数据
    if period==5:
        if len(k)>48*5:
            k = k[-48*5:]
            d = d[-48*5:]
    else:
        if len(k)>16*5:
            k = k[-16*5:]
            d = d[-16*5:]
    shared.toRedis({'k':k,'date':d,'base':base,"ver":3},cacheName,ex=5*24*3600)
    return True,k[-n:],d[-n:]

#当前是交易时间
def isTransTime():
    to = datetime.today()
    if to.weekday()>=0 and to.weekday()<=4 and to.hour>=9 and to.hour<=14:
        if to.hour==9 and to.minute<15: #包括集合竞价阶段
            return False
        return True
    return False

def logCheckResult(code,period,source,checkdata,date=None):
    log.warning(u"logCheckResult '%s' '%s' %s 数据和日线数据不一致"%(code,period,str(date)))
    log.warning(u"\nsource:%s\nnew:%s"%(str(source),str(checkdata)))
    cacheName = "k%s_%s"%(str(period).lower(),code.lower())
    b,cache = shared.fromRedis(cacheName)
    if b:
        k = cache['k']
        d = cache['date']
        base = cache['base']
        checkK(code,period,k,d,base,0)

#判断d是不是一个有效的k时间
def isValidKDate(d,period):
    n = int(period/5)
    for i in range(len(k5date)):
        if k5date[i][0]==d.hour and k5date[i][1]==d.minute:
            return (i+1)%n==0
    return False

#将下载数据附加在k,d数据上
def appendK(code,period,k,d):
    if code[0]=='B' or code[0]=='b': #看看是不是em分类和概念
        code2i = get_em_code2i()
        if code in code2i:
            return appendEMK(code,period,k,d)

    if period==5 or period==15:
        b,nk,nd = K(code,period,32 if period==15 else 96)
    elif type(period)==int:
        b,nk,nd = K(code,5,96)
        if b:
            bi=0
            for i in range(len(nd)):
                if isValidKDate(nd[i][0],period):
                    bi = i+1
                    break
            nk,nd = stock.mergeK(nk[bi:],nd[bi:],int(period/5))
    elif period=='d':
        b,nk,nd = xueqiuKday(code,5)
        #这里对昨天的k15数据计算得到的日线数据和雪球日线数据进行校验
        #问题来源：发现新浪的15分钟深圳成指数据全天求和雪球日线成交量不一致
        #=======================================================
        if b and len(k)>0 and len(nk)>1:
            for i in range(len(d)-1,-1,-1):
                if d[i][0]==nd[-2][0]:#找到校验位置
                    dev = nk[-2]/k[i] 
                    if np.abs(dev-1).max()>0.05:
                        #如果仅仅是成交量偏差，做偏差纠正处理
                        if np.abs(dev[0]-1).max()>0.05:
                            nk[-1][0] = nk[-1][0]/dev[0]
                        else:
                            logCheckResult(code,period,k[i],nk[-2],d[i][0])
                            log.error("差异：%s"%dev)
                    break
        #校验处理完成
        #=======================================================        
    else:
        return False,k,d
    if b and len(d)>0:
        bi = -1
        for i in range(len(nd)-1,-1,-1):
            if d[-1][0]==nd[i][0]:
                bi = i
        if bi!=-1:
            D = copy.copy(d)
            for i in range(bi+1,len(nd)):
                D.append(nd[i])
            if len(nd)-bi-1>0:
                return b,np.vstack((k,nk[bi+1:])),D
    return b,k,d

#以k15为基础给出当日的k数据，成交量为预估
#返回两天的数据，最后一天是预测，倒数第二天是小级别计算出的日线，可以用于校验
#返回b,np.array([volume,open,high,low,close]),[(date,)...]
def xueqiuKday(code,period):
    N = 16 if period==15 else 48
    b,k,d = K(code,period,2*N)
    if b:
        dd = date(d[-1][0].year,d[-1][0].month,d[-1][0].day)
        lasti = None
        for i in range(len(k)-1,-1,-1):
            it = d[i][0]
            it_dd = date(it.year,it.month,it.day)
            if dd!=it_dd:
                yesterday_dd = it_dd
                lasti = i
                break
        if lasti is None:
            log.error("xueqiuKday lasti=None,%s,%s \nk=%s\nd=%s"%(code,period,str(k),str(d)))
            return False,0,0
        #0 volume,1 open,2 high,3 low,4 close
        yesterday = k[lasti-N+1:lasti+1,:]
        today = k[lasti+1:,:]
        if len(today)==0 or len(yesterday)==0:
            return False,0,0
        i = len(today)
        volume = yesterday[:,0].sum()*today[:,0].sum()/yesterday[0:i,0].sum() #简单的按比例算
        return True,np.array([
            [yesterday[:,0].sum(),yesterday[0,1],yesterday[:,2].max(),yesterday[:,3].min(),yesterday[-1,4]],
            [volume,today[0][1],today[:,2].max(),today[:,3].min(),today[-1][4]]
        ]),[(yesterday_dd,),(dd,)]
    return False,0,0

#自选全部
def xueqiuList():
    uri = """https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json?size=1000&pid=-1&category=1"""
    return xueqiuJson(uri)

"""
获取eastmoney资金流数据
返回值
{
    "rc": 0,
    "rt": 21,
    "svr": 2887254207,
    "lt": 1,
    "full": 0,
    "data": {
        "code": "BK0480",
        "market": 90,
        "name": "航天航空",
        "tradePeriods": {
            "pre": null,
            "after": null,
            "periods": [
                {
                    "b": 202102240930,
                    "e": 202102241130
                },
                {
                    "b": 202102241300,
                    "e": 202102241500
                }
            ]
        },
        "klines": [
            "2021-02-24 09:31,-35663761.0,18244385.0,17419377.0,-27101763.0,-8561998.0",
            "2021-02-24 09:32,-40625924.0,24647254.0,15978671.0,-32402924.0,-8223000.0",
            "2021-02-24 09:33,-32623975.0,29256173.0,3367804.0,-24332140.0,-8291835.0",
            ...
        ]
    }
}
"""
def emflow(code,timeout=None,tryn=3):
    t = datetime.today()
    n = "emflow_%s_%d"%(code,t.minute)
    b,R = shared.fromRedis(n)
    if b:
        return R #使用最近2分钟的缓存
    ts = math.floor(time.time())
    if code[0]=='B':
        perfix = '90'
    else:
        if code[0]=='S' or code[0]=='s':
            if code[1]=='H' or code[1]=='h':
                perfix = '1'
            else:
                perfix = '0'
            code = code[2:] #去掉前缀SH或者SZ
        elif code=='399001' or code[0]=='1':
            perfix = '0'
        else:
            perfix = '1'
    uri = "http://push2.eastmoney.com/api/qt/stock/fflow/kline/get?cb=jQuery112309731450462414866_%d&\
&lmt=0&klt=1&fields1=f1%%2Cf2%%2Cf3%%2Cf7&fields2=f51%%2Cf52%%2Cf53%%2Cf54%%2Cf55%%2Cf56%%2Cf57%%2Cf58%%2Cf59%%2Cf60%%2Cf61%%2Cf62%%2Cf63%%2Cf64%%2Cf65&ut=b2884a393a59ad64002292a3e90d46a5&\
secid=%s.%s&_=%d"%(ts,perfix,code,ts)
    for i in range(tryn):
        try:
            s = requests.session()
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
                    'Accept-Encoding': 'gzip, deflate'}
            if timeout is None:
                r = s.get(uri,headers=headers)
            else:
                r = s.get(uri,headers=headers,timeout=timeout)
            if r.status_code==200:
                bi = r.text.find('({"rc":')
                if bi>0:
                    R = json.loads(r.text[bi+1:-2])
                    shared.toRedis(R,n,2*60) #保存一个2分钟的缓存
                    return True,R
        except Exception as e:
            mylog.printe(e)
    return False,None

"""
获取eastmoney kline数据
kd
http://push2his.eastmoney.com/api/qt/stock/kline/get?cb=jQuery112406067857018266605_1616059436272&secid=90.BK0465&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58&klt=101&fqt=0&beg=19900101&end=20220101&_=1616059436273
{
    "rc": 0,
    "rt": 6,
    "svr": 182995714,
    "lt": 1,
    "full": 1,    
    "data": {
        "klines:[
            "2000-01-04,999.64,1028.18,1037.04,987.60,336585,391487000.00,4.94"
            ...
        ]
    },

}
k5
http://push2his.eastmoney.com/api/qt/stock/kline/get?cb=jQuery112406067857018266605_1616059436301&secid=90.BK0465&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58&klt=5&fqt=0&beg=19900101&end=20220101&_=1616059436339
{
    "rc": 0,
    "rt": 6,
    "svr": 182995714,
    "lt": 1,
    "full": 1,    
    "data": {
        "klines:[
            "2021-01-27 09:35,25782.87,25711.66,25854.86,25711.66,1458100,3826018928.00,0.55"
            ...
        ]
    },

}
"""
def emkline(code,period='d',begin='19900101',end='20250101',timeout=None,tryn=3):
    ts = math.floor(time.time())
    if code[0]=='B':
        perfix = '90'
    else:
        if code[0]=='S' or code[0]=='s':
            if code[1]=='H' or code[1]=='h':
                perfix = '1'
            else:
                perfix = '0'
            code = code[2:] #去掉前缀SH或者SZ
        elif code=='399001' or code[0]=='1':
            perfix = '0'
        else:
            perfix = '1'

    if period=='d':
        period = 101
    uri = "http://push2his.eastmoney.com/api/qt/stock/kline/get?cb=jQuery112406067857018266605_1616059436301&secid=%s.%s&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%%2Cf2%%2Cf3%%2Cf4%%2Cf5&fields2=f51%%2Cf52%%2Cf53%%2Cf54%%2Cf55%%2Cf56&klt=%d&fqt=0&beg=%s&end=%s&_=%d"%(perfix,code,period,begin,end,ts)
    for i in range(tryn):
        try:
            s = requests.session()
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
                    'Accept-Encoding': 'gzip, deflate'}
            if timeout is None:
                r = s.get(uri,headers=headers)
            else:
                r = s.get(uri,headers=headers,timeout=timeout)
            if r.status_code==200:
                bi = r.text.find('({"rc":')
                if bi>0:
                    R = json.loads(r.text[bi+1:-2])
                    K = []
                    D = []
                    if 'data' in R and 'klines' in R['data']:
                        klines = R['data']['klines']
                        if period == 101:
                            for k in klines:#"2000-01-04,999.64,1028.18,1037.04,987.60,336585,391487000.00,4.94"
                                #0date 1open 2close 3high 4low 5volume
                                vs = k.split(',')
                                if len(vs)==6:
                                    D.append((datetime.fromisoformat(vs[0]),))
                                    K.append((float(vs[5]),float(vs[1]),float(vs[3]),float(vs[4]),float(vs[2])))
                        else:
                            for k in klines:#"2021-01-27 09:35,25782.87,25711.66,25854.86,25711.66,1458100,3826018928.00"
                                #0date 1open 2close 3high 4low 5volume
                                vs = k.split(',')
                                if len(vs)==6:
                                    D.append((datetime.fromisoformat(vs[0]),))
                                    K.append((float(vs[5]),float(vs[1]),float(vs[3]),float(vs[4]),float(vs[2])))
                    return True,K,D
        except Exception as e:
            mylog.printe(e)
    return False,None,None
"""
主力净流入分布
t=0 行业
t=1 概率
返回数据
{
    "rc": 0,
    "rt": 6,
    "svr": 182995714,
    "lt": 1,
    "full": 1,
    "data": {
        "total": 61,
        "diff": [
            {
                "f12": "BK0451",
                "f13": 90,
                "f14": "房地产",
                "f62": 3829197648
            },
            {
                "f12": "BK0474",
                "f13": 90,
                "f14": "保险",
                "f62": 1386839600
            },
            ...
        ]
    }
}
"""
def emdistribute(t=0,timeout=None):
    ts = math.floor(time.time())
    typeword = "3A2" if t==0 else "3A3"
    uri = "http://push2.eastmoney.com/api/qt/clist/get?cb=jQuery112308140186664104734_%d&pn=1&pz=500&po=1&np=1&fields=f12%%2Cf13%%2Cf14%%2Cf62&fid=f62&fs=m%%3A90%%2Bt%%%s&ut=b2884a393a59ad64002292a3e90d46a5&_=%d"%(ts,typeword,ts)
    try:
        s = requests.session()
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
                'Accept-Encoding': 'gzip, deflate'}
        if timeout is None:
            r = s.get(uri,headers=headers)
        else:
            r = s.get(uri,headers=headers,timeout=timeout)
        if r.status_code==200:
            bi = r.text.find('({"rc":')
            if bi>0:
                R = json.loads(r.text[bi+1:-2])
                return True,R
            else:
                return False,r.text
        else:
            return False,r.reason
    except Exception as e:
        mylog.printe(e)
        return False,str(e)

"""
批量获取em数据,注意返回字段可以任意定制
返回数据
{
    "rc": 0,
    "rt": 6,
    "svr": 182995714,
    "lt": 1,
    "full": 1,
    "data": {
        "total": 61,
        "diff": [
            {
                "f12": "BK0451",
                "f13": 90,
                "f14": "房地产",
                "f62": 3829197648
            },
            {
                "f12": "BK0474",
                "f13": 90,
                "f14": "保险",
                "f62": 1386839600
            },
            ...
        ]
    }
}
可以在个股资金流页面get?cb查找到详细字段
f2 f2/1000当前价格 
f3 f3/100当日涨跌
f5 当日成交量
f6 当日成交额
f8 f6/100换手率 
f9 市盈率
f12 代码
f13 代码前缀 90 板块 1 SH 0 SZ
f14 名称
f62 主力净流入
f66 超大单
f72 大单
f78 中单
f84 小单
"""
def emdistribute2(codes,field='f12,f13,f14,f62',timeout=None,tryn=3):
    ts = math.floor(time.time())
    codelists = ""
    for c in codes:
        perfix = '1'
        code = c
        if c[0]=='S' or c[0]=='s':
            if c[1]=='H' or c[1]=='h':
                perfix = '1'
            else:
                perfix = '0'
            code = c[2:]
        elif c=='399001' or c[0]=='1':
            perfix = '0'
        elif c[0]=='B' or c[0]=='b':
            perfix = '90'
        else:
            perfix = '1'
        codelists += "%s.%s,"%(perfix,code)
    codelists = codelists[:-1]
    n = len(codes)
    uri="https://push2.eastmoney.com/api/qt/ulist/get?cb=jQuery1124046041648531999235_%d&invt=3&pi=0&pz=%d&mpi=2000&secids=%s&ut=6d2ffaa6a585d612eda28417681d58fb&fields=%s&po=1&_=%d"%(ts,n,codelists,field,ts)
    for i in range(tryn):
        try:
            s = requests.session()
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
                    'Accept-Encoding': 'gzip, deflate'}
            if timeout is None:
                r = s.get(uri,headers=headers)
            else:
                r = s.get(uri,headers=headers,timeout=timeout)
            if r.status_code==200:
                bi = r.text.find('({"rc":')
                if bi>0:
                    R = json.loads(r.text[bi+1:-2])
                    return True,R
        except Exception as e:
            mylog.printe(e)
    return False,None

def emdistribute3(codes,timeout=None):
    pass
_em_category = None
#返回stock.flow_em_category
#0id 1name 2code 3prefix 4watch
def get_em_category():
    global _em_category
    if _em_category is None:
        _em_category = stock.query("select * from flow_em_category")
    return _em_category
_em_code2i = None
#返回一个映射表(给出code返回顺序i)
def get_em_code2i():
    global _em_code2i
    if _em_code2i is None:
        emls = get_em_category()
        _em_code2i = {}
        for i in range(len(emls)):
            _em_code2i[emls[i][2]] = i
    return _em_code2i
_em_code2id = None
def get_em_code2id():
    global _em_code2id
    if _em_code2id is None:
        emls = get_em_category()
        _em_code2id = {}
        for i in range(len(emls)):
            _em_code2id[emls[i][2]] = emls[i][0]
    return _em_code2id
def rebuild_em_category():
    global _em_category,_em_code2i,_em_code2id
    _em_category = None
    _em_code2i = None
    _em_code2id = None
#返回(len(timestamp),len(codes))
def emflowRT():
    try:
        t = datetime.today()
        if t.hour==9 and t.minute<30:
            return
        n = "emflowts_%d_%d"%(t.month,t.day)
        k = "emflownp_%d_%d"%(t.month,t.day)
        b,D = shared.fromRedis(n)
        if b and D[-1].minute==t.minute and D[-1].day==t.day:
            return
        if D is None:
            D = []
        b,R = shared.numpyFromRedis(k)
        rr = []
        b,r = emdistribute(0) #行业
        rr.append(r)
        b1,r = emdistribute(1) #概念
        rr.append(r)
        if b and b1:
            code2i = get_em_code2i()
            a = np.zeros((len(code2i),))
            for r in rr:
                if 'data' in r:
                    ls = r['data']['diff']
                    #使用emls的顺序重新组织数据
                    for it in ls:
                        code = it['f12']
                        if code in code2i:
                            i = code2i[code]
                            a[i] = it['f62']
            
            #对那些不是个股进行数据单独下载
            alls = get_em_category()
            codes = []
            for c in alls:
                if c[2][0] != 'B':
                    codes.append(c[2])
            #每一个批量不要多于100个
            for i in range(0,len(codes),100):
                b,r = emdistribute2(codes[i:i+100])
                if b:
                    if 'data' in r:
                        ls = r['data']['diff']
                        #使用emls的顺序重新组织数据
                        for it in ls:
                            v = ls[it]
                            code = v['f12']

                            if 'SH'+code in code2i:
                                i = code2i['SH'+code]
                                if i<len(code2i):
                                    a[i] = v['f62']
                            elif 'SZ'+code in code2i:
                                i = code2i['SZ'+code]
                                if i<len(code2i):
                                    a[i] = v['f62']
                            elif code in code2i:
                                i = code2i[code]
                                if i<len(code2i):
                                    a[i] = v['f62']
            if R is None:
                RR = a
            else:
                RR = np.vstack((R,a))
            D.append(datetime(t.year,t.month,t.day,t.hour,t.minute,0))

            shared.numpyToRedis(RR,k,ex=1*24*3600) #保留1天
            shared.toRedis(D,n,ex=1*24*3600)
    except Exception as e:
        mylog.printe(e)

"""
对emflowRT进行改进,对flow_em_category中的全部进行监控
返回当前的数据plane
[[0 price,1 当日涨幅,2 volume,3 larg,4 big,5 mid,6 ting]]
"""
def emflowRT2():
    try:
        t = datetime.today()
        if not (stock.isTransTime() and stock.isTransDay()):
            return
        n = "emflowts2_%d_%d"%(t.month,t.day)
        k = "emflownp2_%d_%d"%(t.month,t.day)
        b,D = shared.fromRedis(n)
        if b and D[-1].minute==t.minute and D[-1].day==t.day:
            return
        if D is None:
            D = []
        b,R = shared.numpyFromRedis(k)
            #对那些不是个股进行数据单独下载
        alls = get_em_category()
        code2i = {}
        codes = []
        etfs = []
        for i in range(len(alls)):
            c = alls[i]
            code2i[c[2]] = i
            codes.append(c[2])
            if c[3]=='2':
                etfs.append(c[2])
        #每一个批量不要多于100个
        a = np.zeros((len(alls),1,7))
        for i in range(0,len(codes),100):
            b,r = emdistribute2(codes[i:i+100],'f12,f13,f2,f3,f5,f66,f72,f78,f84')
            if b:
                if 'data' in r:
                    ls = r['data']['diff']
                    #使用emls的顺序重新组织数据
                    for it in ls:
                        v = ls[it]
                        perfix = v['f13']
                        if perfix==90:
                            code = v['f12']
                        else:
                            code = ('SH'+v['f12']) if perfix==1 else ('SZ'+v['f12'])
                        if code in code2i:
                            #0 price,1 当日涨幅,2 volume,3 larg,4 big,5 mid,6 ting
                            j = code2i[code]
                            if j<len(code2i) and v['f2'] is not None:
                                if code in etfs:
                                    a[j,0,0] = int(v['f2'])/1000.0
                                else:
                                    a[j,0,0] = int(v['f2'])/100.0
                                if a[j,0,0]==0 and R is not None:
                                    a[j,0,0] = R[j,-1,0]
                                if a[j,0,1]==0 and R is not None:
                                    a[j,0,1] = R[j,-1,1]
                                a[j,0,1] = int(v['f3'])/100.0
                                a[j,0,2] = v['f5']
                                a[j,0,3] = v['f66']
                                a[j,0,4] = v['f72']
                                a[j,0,5] = v['f78']
                                a[j,0,6] = v['f84']
                        else:
                            print("没有成功获取数据 %s"%(code))
            else:
                print("%s emflowRT2数据加装失败..."%str(t))
                return
        if np.count_nonzero(a[:,0,0])<a.shape[0]*0.95: #超过一定比率下载失败就不更新数据了
            print("%s emflowRT2数据更新出现较多的数据错误 %d/%d"%(str(t),np.count_nonzero(a[:,0,0]),a.shape[0]))
            return None
        if R is None:
            RR = a
        else:
            RR = np.hstack((R,a))
        D.append(datetime(t.year,t.month,t.day,t.hour,t.minute,0))

        shared.numpyToRedis(RR,k,ex=7*24*3600) #保留7天
        shared.toRedis(D,n,ex=7*24*3600)
        return a
    except Exception as e:
        mylog.printe(e)
    return None
"""
将eastmoney资金流数据存入数据库中
"""
def emflow2db():
    try:
        print("将资金流数据下载保存到数据库`")
        count = 0
        """
        将行业分类和概念分类放入到数据库
        """
        needrebuild = False
        ls = get_em_category()
        code2id = get_em_code2id()
        for i in range(2):
            b,r = emdistribute(i)
            if b and 'data' in r:
                lss = r['data']['diff']
                for s in lss:
                    code = s['f12']
                    if code not in code2id:
                        needrebuild = True
                        qss = stock.query("select max(company_id) from flow_em_category")
                        company_id = qss[0]+1
                        stock.execute("insert ignore into flow_em_category (name,code,prefix,watch,company_id) values ('%s','%s',%d,0)"%(s['f14'],code,s['f13']+i,company_id))
        if needrebuild:
            rebuild_em_category()
            ls = get_em_category()
            code2id = get_em_code2id()
        ELS = []

        for j in range(3):
            for c in ls:
                #0id 1name 2code 3prefix 4watch
                for i in range(10): #重试9次不行就报告错误并忽略
                    if i==9:
                        print("emflow2db download fail %s,%s"%(c[1],c[2]))
                        ELS.append(c)
                        break
                    try:
                        b,R = emflow(c[2])
                        if b and 'data' in R and R['data'] is not None:
                            klines = R['data']['klines']
                            QS = ""
                            count=count+1
                            for k in klines:
                                vs = k.split(',')
                                if len(vs)==6:
                                    QS+="(%d,'%s',%s,%s,%s,%s),"%(code2id[c[2]],vs[0],vs[2],vs[3],vs[4],vs[5])
                            #print("%s insert flow"%(c[2]))
                            if len(QS)>0:
                                stock.execute("insert ignore into flow_em values %s"%QS[:-1])
                            break
                        else:
                            print("emflow2db 下载的数据存在问题, %s"%(str(c)))
                            break
                    except Exception as e:
                        print(c)
                        mylog.printe(e)
            if len(ELS)>0:
                ls = ELS #存在错误，将错误在处理一次
                ELS = []
            else:
                break
        print("emflow2db %d"%count)
    except Exception as e:
        mylog.printe(e)

"""
N加载N天数据
返回一个时间戳列表，和一个numpy矩阵,shape=(len(timestamp),len(codes))
"""
def mainflow(codes,N=3):
    kdd = stock.query('select date from kd_xueqiu where id=8828 order by date desc limit %d'%N)
    after = kdd[-1][0]
    D = []
    R = None
    t2i = {}
    code2id =get_em_code2id()
    for j in range(len(codes)):
        c = codes[j]
        F = stock.query("select * from flow_em where timestamp>='%s' and id=%d"%(stock.dateString(after),code2id[c]))
        if R is None:
            for i in range(len(F)):
                D.append(F[i][1])
                t2i[F[i][1]] = i
            R = np.zeros((len(D),len(codes)))
        if len(F)==len(D): #粗略处理，对于数据丢失没有做处理
            for i in range(len(F)):
                R[i,j] = F[i][4]+F[i][5]
        elif len(F)<len(D):
            for i in range(len(F)):
                if F[i][1] in t2i:
                    R[t2i[F[i][1]],j] = F[i][4]+F[i][5]
        else:
            print("mainflow 第一组数据不全")
    return R,D

"""
将历史数据叠加最新的实时数据
"""
def mainflowrt(codes,R=None,D=None):
    t = datetime.today()
    n = "emflowts2_%d_%d"%(t.month,t.day)
    k = "emflownp2_%d_%d"%(t.month,t.day)
    b,d = shared.fromRedis(n)
    b1,r = shared.numpyFromRedis(k)
    code2i = get_em_code2i()

    if R is None: #当天数据
        if b and b1:
            s = np.zeros((len(d),len(codes)))
            for i in range(len(codes)):
                j = code2i[codes[i]]
                if j<r.shape[0]:
                    s[:,i] = r[j,:,3]+r[j,:,4]
            return s,d
        else:
            return np.zeros((0,0)),[]
    #参数检查
    if R.shape[0]!=len(D):
       raise "R.shape[0]!=len(D)"
    if R.shape[1]!=len(codes):
        raise "R.shape[1]!=len(codes)"
    
    if b and b1 and D[-1]<d[0]:
        s = np.zeros((len(d),len(codes)))
        for i in range(len(codes)):
            s[:,i] = r[code2i[codes[i]],:,3]+r[code2i[codes[i]],:,4]
        return np.vstack((R,s)),D+d
    else:
        return np.copy(R),D

#将单个em kline下载并保存到db中
def emk2db(db,id,code,period):
    try:
        if period==5:
            twords = 'timestamp'
            t2s = stock.timeString
        else:
            twords = 'date'
            t2s = stock.dateString
        lss = stock.query("select * from %s where id=%d order by %s desc limit 1"%(db,id,twords))
        if len(lss)==0:
            begin = '19900101'
        else:
            t = lss[0][1]
            begin = "%s%02d%02d"%(t.year,t.month,t.day)
        b,K,D = emkline(code,period,begin)
        if b:
            #print('emk2db %s %s'%(code,period))
            wd = "id,%s,volume,open,high,low,close"%twords
            for j in range(0,len(D),100): #每次刷入100个数据
                s = ""
                for i in range(j,j+100):
                    if i<len(K):
                        k = K[i]
                        t = t2s(D[i][0])
                        s += "(%d,'%s',%f,%f,%f,%f,%f),"%(id,t,k[0],k[1],k[2],k[3],k[4])
                if len(s)>0:
                    stock.execute("insert ignore into %s (%s) values %s"%(db,wd,s[:-1]))
        else:
            print('emk2db %s %s 下载失败'%(code,period))
    except Exception as e:
        mylog.printe(e)
"""
将em的分类和概念的kd,k5下载存入到kd_em,k5_em

kd_em或者k5_em中仅仅存放em的分类和概念
"""
def emkline2db():
    #保存BK开头的全部
    print("将EM分类和概念的k线数据保存到数据库")
    lss = stock.query("select * from flow_em_category where code like'BK%'")
    for c in lss:
        emk2db('kd_em',c[5],c[2],'d')
        emk2db('k5_em',c[5],c[2],5)
    print("emkline2db %d"%len(lss))

"""
返回当天的资金流数据
"""
def getTodayFlow(code):
    code2i = get_em_code2i()
    t = datetime.today()
    if code in code2i:
        n = "emflowts2_%d_%d"%(t.month,t.day)
        k = "emflownp2_%d_%d"%(t.month,t.day)
        b,D = shared.fromRedis(n)
        b1,R = shared.numpyFromRedis(k)
        if b and b1:
            f = []
            d = []
            j = code2i[code]
            for i in range(len(D)):
                d.append((D[i],))
                f.append(R[j,i,3:])
            return True,f,d
    else:
        name = "flow_%d_%d"%(t.month,t.day) #sinaFlow
        b,a = shared.fromRedis(name)
        if b:
           f = []
           d = []
           for k in a:
               f.append(k[1:])
               d.append((k[0],))
           return True,f,d
    return False,None,None

"""
返回code的资金流数据
如果没有发现code就使用sinaFlow数据
"""
_getflowcache = {}
def getFlow(code,lastday=None):
    #这里对数据进行缓存避免多次操作数据库
    global _getflowcache
    if code not in _getflowcache:
        after = stock.dateString(date.today()-timedelta(days=365 if lastday is None else lastday))
        b,flowk,flowd = stock.loademFlow(code,after)
        if not b:
            flowk,flowd = stock.loadFlow(after)
        _getflowcache[code] = [flowk,flowd]
    
    flowk,flowd = _getflowcache[code]

    b,k,d = getTodayFlow(code)
    if b and d[-1][0]>flowd[-1][0]:#叠加
        endt = flowd[-1][0]
        nfk = []
        for i in range(len(d)):
            if d[i][0]>endt:
                nfk.append(k[i])
                flowd.append(d[i])

        flowk = np.vstack((flowk,nfk))
        _getflowcache[code][0] = flowk
    return flowk,flowd

"""
取得今天的分时
[[0 price,1 当日涨幅,2 volume,3 larg,4 big,5 mid,6 ting]]
"""
def getTodayRT(t=None):
    if t is None:
        t = datetime.today()
    nname = "emflowts2_%d_%d"%(t.month,t.day)
    kname = "emflownp2_%d_%d"%(t.month,t.day)
    b,D = shared.fromRedis(nname)
    b1,R = shared.numpyFromRedis(kname)
    if b and b1:
        return True,R,D
    else:
        return False,None,None
#k5时序迭代器 (时间，开始位置，结束位置)
class period5Iterator:
    def __init__(self,d):
        self._d = d
        self._i = 0 #处理的当前位置
        self._e = len(d) #处理的结束位置
    def __iter__(self):
        return self
    def __next__(self):
        bi = self._i
        t = next_k_timestamp(self._d[self._i])
        for i in range(bi,self._e):
            if self._d[i]>t:
                self._i = i
                return t,bi,self._i
        raise StopIteration
"""
appendK在处理EM分类和概念时实时的从emflowts2中取得k线数据
"""
def appendEMK(code,period,k,d):
    code2i = get_em_code2i()
    t = datetime.today()
    if len(d)>0:
        #已经是最新的数据了不需要更新
        if d[-1][0].year==t.year and d[-1][0].month==t.month and d[-1][0].day==t.day:
            return True,k,d
    if code in code2i:
        nname = "emflowts2_%d_%d"%(t.month,t.day)
        kname = "emflownp2_%d_%d"%(t.month,t.day)
        b,D = shared.fromRedis(nname)
        b1,R = shared.numpyFromRedis(kname)
        if b and b1:
            j = code2i[code]
            if period=='d':
                bi = 0
                for bi in range(len(D)):#排除掉开盘前的数据
                    if (D[bi].hour==9 and D[bi].minute>=30) or D[bi].hour>9:
                        break
                if bi!=len(D)-1:
                    open1 = R[j,bi,0]
                    high = np.max(R[j,bi:,0])
                    low = np.min(R[j,bi:,0])
                    close1 = R[j,-1,0]
                    volume = R[j,-1,2]
                    nk = (volume,open1,high,low,close1)
                    return True,np.vstack((k,nk)),d+[(date.today(),)]
                else:
                    return True,k,d
            else:
                nk = []
                nd = []
                for t,bi,ei in period5Iterator(D):
                    nd.append((t,))
                    open1 = R[j,bi,0]
                    high = np.max(R[j,bi:ei,0])
                    low = np.min(R[j,bi:ei,0])
                    close1 = R[j,ei-1,0]
                    volume = R[j,ei-1,2]-R[j,bi,2]
                    nk.append((volume,open1,high,low,close1))
                if len(nk)>0:
                    if period!=5:
                        nk = np.array(nk).reshape(-1,5)
                        nk,nd = stock.mergeK(nk,nd,int(period/5))
                    return True,np.vstack((k,nk)),d+nd
    return False,k,d
