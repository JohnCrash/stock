import matplotlib.pyplot as plt
import numpy as np
from numpy.core.fromnumeric import compress
import requests
import time
import subprocess
import ipywidgets as widgets
from IPython.display import display,update_display,clear_output
from datetime import date,datetime,timedelta
import json
from . import mylog
from . import config
from . import shared
from . import xueqiu
from . import stock
from . import status
from . import kline
from . import monitor
from . import ziprt

log = mylog.init('tool.log',name='tool')
"""
标记msci个股，数据来自于EM
在company中增加字段msci
"""
def updatemsci(timeout=None):
    N = 50 #每次50个
    i = 1
    codes = []
    total = 0
    print('开始从em下载msci列表:')
    for i in range(1,16):
        uri = "http://push2.eastmoney.com/api/qt/clist/get?cb=jQuery1123044091579095858546_1615970378679&fid=f62&po=1&pz=%d&pn=%d&np=1&fltt=2&invt=2&ut=b2884a393a59ad64002292a3e90d46a5&fs=b%%3ABK0821&fields=f12%%2Cf14%%2Cf2%%2Cf3%%2Cf62%%2Cf184%%2Cf66%%2Cf69%%2Cf72%%2Cf75%%2Cf78%%2Cf81%%2Cf84%%2Cf87%%2Cf204%%2Cf205%%2Cf124"%(N,i)
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
                    if 'data' in R and 'diff' in R['data']:
                        total = R['data']['total']
                        for it in R['data']['diff']:
                            code = it['f12']
                            print(code)
                            codes.append(code)
                        if total==len(codes) or len(R['data']['diff'])!=N:
                            print('下载列表完成')
                            break
                else:
                    print('updatemsci: '+str(r.text))
                    break
            else:
                print('updatemsci:'+str(r.reason))
                break
        except Exception as e:
            log.error("updatemsci:"+"ERROR:"+str(e))
            return False,str(e)
    print('总共发现 %d ,下面开始更新company'%len(codes))

    stock.execute("update stock.company set msci=0")
    companys = stock.query('select * from company')
    code2c = {}
    for i in range(len(companys)):
        c = companys[i]
        code2c[c[1][2:]] = c
    for c in codes:
        if c in code2c:
            C = code2c[c]
            print('update %s %s'%(C[1],C[2]))
            stock.execute("update stock.company set msci=1 where code='%s'"%C[1])
        else:
            print('company 中没有此代码:%s'%c)
    return codes

#将flow_em_category中的编码为数字的加上前缀SH SZ
def flowemcategoryshsz():
    companys = stock.query("select * from company")
    code2c = {}
    for c in companys:
        code2c[c[1][2:]] = c
    lss = stock.query("select * from flow_em_category")
    for c in lss:
        if c[2][0]!='B' and c[2][0]!='S':
            if c[2] in code2c:
                stock.execute("update flow_em_category set code='%s' where code='%s'"%code2c[c[2]][1],c[2])
            else:
                print("not find "+c[2])

#数据库flow_em_category的code丢失，回复
def flowemcategoryre():
    #先回复分类和概念
    for i in range(2):
        b,r = xueqiu.emdistribute(i)
        if b and 'data' in r:
            lss = r['data']['diff']
            for s in lss:
                code = s['f12']
                name = s['f14']
                stock.execute("update flow_em_category set code='%s' where name='%s'"%(code,name))
def flowemcategoryre2():
    #回复公司代码
    lss = stock.query("select * from flow_em_category where code=''")
    company = stock.query("select * from company")
    name2c = {}
    for c in company:
        name2c[c[2]] = c
    for c in lss:
        name = c[1]
        if name in name2c:
            code = name2c[c[1]][1]
            stock.execute("update flow_em_category set code='%s' where name='%s'"%(code,name))


#给flow_em_category BK开头的代码安排id
def flowemaid():
    lss = stock.query("select * from flow_em_category where code like 'BK%'")
    id = 90000
    for c in lss:
        id = id+1
        stock.execute("update flow_em_category set company_id=%d where code='%s'"%(id,c[2]))

#将flow_em_category 中的非BK开头的id设置号
def flowemaid2():
    lss = stock.query("select * from flow_em_category where code not like 'BK%'")
    for c in lss:
        idds = stock.query("select id from company where code='%s'"%(c[2]))
        if len(idds)==1:
            id = idds[0][0]
            stock.execute("update flow_em_category set company_id=%d where code='%s'"%(id,c[2]))

#排除flow中代码相同的          
def flowempc():
    lss = stock.query("select * from flow_em_category")
    R = {}
    print("--")
    for c in lss:
        if c[2] in R:
            print('重复的：'+c[2])
        else:
            R[c[2]] = c

#取得基金持仓和占比
def getetfcc(code):
    uri = "https://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code=%s&topline=10&year=2020&month=&rt=0.5556118613867067"%(code[2:])
    try:
        s = requests.session()
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
                'Accept-Encoding': 'gzip, deflate'}
        r = s.get(uri,headers=headers)
        qs = 'quote.eastmoney.com/'
        qslen = len(qs)
        if r.status_code==200:
            i = 0
            result = []
            R = {}
            while True:
                i = r.text.find(qs,i)
                if i>0:
                    #print(i,r.text[i+qslen:i+qslen+8])
                    C = r.text[i+qslen:i+qslen+8].upper()
                    if C not in R:
                        R[C] = C
                        result.append(C)
                    i = i+qslen
                else:
                    return result
        else:
            print('getetfcc:'+str(r.reason))
    except Exception as e:
        print("getetfcc:"+str(e))
    return []

#将etf持仓加入到资金跟踪里面
def etfcc():
    etfs = stock.query("select * from flow_em_category where name like '%%ETF'")
    companys = stock.query("select * from company")
    code2c = {}
    for c in companys:
        code2c[c[1]] = c
    for c in etfs:
        #使用em数据将ETF持仓加入到flow_em_category中去
        print("处理%s %s:"%(c[1],c[2]))
        codes = getetfcc(c[2])
        for c in codes:
            lss = stock.query("select * from flow_em_category where code='%s'"%c)
            if len(lss)==0:
                prefix = 0 if c[1]=='Z' else 1
                qs = "insert ignore into flow_em_category (name,code,prefix,watch,company_id) values ('%s','%s',%d,6,%d)"%(code2c[c][2],c,prefix,code2c[c][0])
                print(qs)
                stock.execute(qs)

#将etf持仓放入emlist
def eft2emlist():
    etfs = stock.query("select * from flow_em_category where name like '%%ETF'")
    companys = stock.query("select * from company")
    code2c = {}
    for c in companys:
        code2c[c[1]] = c
    for c in etfs:
        #使用em数据将ETF持仓加入到flow_em_category中去
        print("处理%s %s:"%(c[1],c[2]))
        codes = getetfcc(c[2])
        QS = ""
        for code in codes:
            QS += "('%s','%s'),"%(c[2],code)
        stock.execute("insert ignore into emlist (emcode,code) values %s"%QS[:-1])

"""
检查数据库k5_xueqiu,kd_xueqiu,k5_em,kd_em看看最近那些没有正常更新
同时检查flow,flow_em
s = 'all' 检查全部
s = 'xueqiu' 仅仅检查xueqiu
s = 'em' 仅仅检查em
reupdate = True,删除错误数据重新下载
reupdate = False,不做重新下载操作
"""
def checkdb(s='all',reupdate=False):
    t = datetime.today()
    if stock.isTransDay() and t.hour>=15:
        d = stock.dateString(t)
    else:
        lss = stock.query("select date from kd_xueqiu where id=8828 order by date desc limit 1")
        d = stock.dateString(lss[0][0])
    def setupdate(id):
        if reupdate:
            stock.execute("update company set `ignore`=0 where id=%d"%(id))
    if s=='all' or s=='xueqiu':
        companys = stock.query("select id,code,name from company")
        print("检查k5_xueqiu和kd_xueqiu...")
        for c in companys:
            try:
                id = c[0]
                lss = stock.query("select date from kd_xueqiu where id=%d and date='%s'"%(id,d))
                if len(lss)==0:
                    qs = stock.query("select date from kd_xueqiu where id=%d order by date desc limit 1"%(id))
                    print('kd_xueqiu最后更新 %s %s'%(str(c),str(qs)))
                    setupdate(id)
                lss = stock.query("select timestamp from k5_xueqiu where id=%d and timestamp>'%s'"%(id,d))
                if len(lss)==0:
                    qs = stock.query("select timestamp from k5_xueqiu where id=%d order by timestamp desc limit 1"%(id))
                    if len(qs)>0:
                        print('k5_xueqiu最后更新 %s %s'%(str(c),str(qs)))
                    else:
                        print('k5_xueqiu中没有 %s'%(str(c)))
                    setupdate(id)
                elif len(lss)!=48:
                    print('k5更新数量错误 %s %d'%(str(c),len(lss)))
                    if reupdate: #重新更新
                        stock.execute("delete from k5_xueqiu where id=%d and timestamp>'%s'"%(id,d))
                    setupdate(id)
            except Exception as e:
                mylog.printe(e)
                print(str(c))
        if reupdate:
            r = subprocess.run(['node',config.download_js])
    if s=='all' or s=='em':
        print("检查k5_em和kd_em...")
        ems = stock.query("select company_id,code,name from flow_em_category where code like'BK%'") #kd_em或者k5_em中仅仅存放em的分类和概念
        for c in ems:
            try:
                id = c[0]
                lss = stock.query("select date from kd_em where id=%d and date='%s'"%(id,d))
                if len(lss)==0:
                    qs = stock.query("select date from kd_em where id=%d order by date desc limit 1"%(id))
                    print('kd_em最后更新 %s %s'%(str(c),str(qs)))
                lss = stock.query("select timestamp from k5_em where id=%d and timestamp>'%s'"%(id,d))
                if len(lss)==0:
                    qs = stock.query("select timestamp from k5_em where id=%d order by timestamp desc limit 1"%(id))
                    if len(qs)>0:
                        print('k5_em最后更新 %s %s'%(str(c),str(qs)))
                    else:
                        print('k5_em中没有 %s'%(str(c)))
                elif len(lss)!=48:
                    print('k5_em更新数量错误 %s %d'%(str(c),len(lss)))
            except Exception as e:
                mylog.printe(e)
                print(str(c))

"""
删除一个退市的公司
"""
def deletecompany(code):
    com = stock.query("select id,code,name from company where code='%s'"%code)
    if len(com)>0:
        c = com[0]
        print("删除公司 %s"%str(c))
        stock.execute("insert ignore into company_delisting (id,code,name) values (%d,'%s','%s')"%(c[0],c[1],c[2]))
        stock.execute("delete from company where code='%s'"%code)
    else:
        print("不存在公司 %s"%code)

#将概念设置为prefix=91
def setglian():
    b,r = xueqiu.emdistribute(1)
    if b:
        lss = r['data']['diff']
        for s in lss:
            code = s['f12']
            stock.execute("update flow_em_category set prefix=91 where code='%s'"%code)    

"""            
#a = monitor.getMaRise()
#print(a)
"""
"""
A = monitor.getTodayTop('90')
B = monitor.getTodayTop('91',15)
print(A)
print(B)
print(monitor.getDTop('90',3))
print(monitor.getDTop('91',15))
"""
def moniterLoop():
    companys = xueqiu.get_company_select()
    code2c = {}
    for c in companys:
        code2c[c[1]] = c
    E = None
    #b,r,d = xueqiu.getTodayRT()
    #for i in range(1,r.shape[1]):
    if True:
        #print(d[i])
        e,E = monitor.moniter_loop()#(E,i)
        m2s = {
            'fl_top':'分类榜',
            'gn_top':'概念榜',
            'fl_topup':'上分类榜',
            'gn_topup':'上概念榜',
            'bollup':'boll打开',
            'maclose':'冲高回落',
            'highup':'高开',
            'fastup':'快速上涨'
        }
        for it in e.items():
            com = code2c[it[0]]
            s = "'%s' "%com[2]
            for x in it[1]:
                ty = x[0]
                pr = x[1]
                t = x[2]
                s += '%s '%(m2s[ty])
            print(s)
    print(E['bollopen'])
    print("=====================")
    print(E['maclose'])
    #xueqiu.Timer(60,moniterLoop)

"""
发现那些大资金流入最稳健的
"""
def searchstrongflow():
    companys = xueqiu.get_company_select()
    t = date.today()
    b,k,d = xueqiu.getTodayRT()
    t2 = t
    if not b:
        for i in range(1,7):
            t2 = t-timedelta(days=i)
            b,k,d = xueqiu.getTodayRT(t2)
            if b:
                break
            if i==6:
                return
    S = []
    for i in range(k.shape[0]):
        if companys[i][3]=='90' or companys[i][3]=='91':
            mflow = k[i,:,3]+k[i,:,4]
            inn = 1
            outn = 1
            for j in range(1,k.shape[1]):
                #if mflow[j]>mflow[j-1]:
                if k[i,j,0]>k[i,j-1,0]:
                    inn+=1
                else:
                    outn+=1
            S.append((inn/outn,i))
    S = sorted(S,key=lambda it:it[0],reverse=True)
    R = []
    for s in S:
        R.append(s[1])
    shared.toRedis(R[:8],'monitor',ex=24*3600)

"""
更新period_sequence
"""
def update_period_sequence():
    for p in [240,60,30,15,5]:
        xueqiu.rebuild_period_sequence(p)

"""
返回最近的实时数据
"""
def get_last_rt(t):
    b,k,d = xueqiu.getTodayRT(t)
    t2 = t
    if not b:
        for i in range(1,7):
            t2 = t-timedelta(days=i)
            b,k,d = xueqiu.getTodayRT(t2)
            if b:
                break
    return t2,k,d

"""
压缩rt数据
"""
def ziprt2():
    import pickle
    import zlib
    b,k,d = get_last_rt(datetime.today())
    if b:
        info = pickle.dumps([k.shape,k.dtype.name])
        length = int(len(info))
        encoded = length.to_bytes(2,byteorder='big')+info+k.tobytes()
        data = zlib.compress(encoded)
        with open('d://rt.dat', 'wb') as f:
            f.write(data)

def ziprtopen():
    import pickle
    import zlib
    with open('d://rt.dat', 'rb') as f:
        data = f.read()
        encoded = zlib.decompress(data)
        length = int.from_bytes(encoded[:2],byteorder='big')
        info = pickle.loads(encoded[2:2+length])
        a = np.frombuffer(encoded,dtype=info[1],offset=2+length).reshape(info[0])
        return True,a
    return False,None

def zqxy(prefix='91',N=3):
    k,d = xueqiu.get_period_k(15)
    companys = xueqiu.get_company_select()
    zqk = []
    zqmin = []
    zqmax = []
    zqd = []
    def calc_zqxy(z,i,k,d):
        p = k[z,i]
        v = 0
        minv = 99999
        maxv = 0
        b = False
        for j in range(i+15,i+15+16):
            if k.shape[1]>j and k[z,j]>p:
                v+=1
            if k.shape[1]>j and k[z,j]>maxv:
                maxv = k[z,j]
                b = True
            if k.shape[1]>j and k[z,j]<minv:
                minv = k[z,j]
                b = True
        if b:
            return v/16.,minv,maxv
        else:
            return v/16.,k[z,-1],k[z,-1]
    for i in range(len(d)):
        if d[i][0].hour==10 and d[i][0].minute==0:
            sni = np.argsort((k[:,i]-k[:,i-3])/k[:,i-3])
            v = 0
            minV = 0
            maxV = 0
            n = 0
            S = []
            for j in range(-1,-len(d),-1):
                z = sni[j]
                if companys[z][3]==prefix and k[z,i]>0:
                    vv,minv,maxv = calc_zqxy(z,i,k,d)
                    minV += ((minv-k[z,i])/k[z,i])/N
                    maxV += ((maxv-k[z,i])/k[z,i])/N
                    v += vv/N
                    n+=1
                    #print(n,companys[z][2])
                    S.append((n,companys[z][2]))
                    if n>=N:
                        break
            zqmin.append(minV*100)
            zqmax.append(maxV*100)
            zqk.append(v)
            zqd.append((datetime(year=d[i][0].year,month=d[i][0].month,day=d[i][0].day),))
            print(zqd[-1][0],S)

    fig,axs = plt.subplots(2,1,figsize=(32,16))
    x = np.arange(len(zqk))
    xticks = []
    for i in range(len(zqk)):
        xticks.append(i)
    axs[0].xaxis.set_major_formatter(kline.MyFormatter(zqd,'m-d'))
    axs[0].plot(x,zqk)
    axs[0].axhline(y=0.5,color='black',linestyle='dotted')
    axs[0].set_xticks(xticks)
    axs[0].grid(True)
    axs[1].xaxis.set_major_formatter(kline.MyFormatter(zqd,'m-d'))
    axs[1].plot(x,zqmin,label='min')
    axs[1].plot(x,zqmax,label='max')
    axs[1].grid(True)
    axs[1].set_xticks(xticks)
    axs[1].legend()
    plt.show()

"""
将分类和概念的个股列表存入到emlist中去
"""
def saveemlist():
    companys = xueqiu.get_company_select()
    alls = stock.query("select code from company")
    codenum2code = {}
    for c in alls:
        codenum2code[c[0][2:]] = c[0]
    for com in companys:
        QS = stock.query("select * from emlist where emcode='%s'"%com[1])
        if (com[3]=='90' or com[3]=='91') and len(QS)==0:
            b,R = xueqiu.emgllist(com[1])
            if b:
                print(com[1],len(R))
                QS = ""
                for it in R:
                    if 'f12' in it and it['f12'] in codenum2code:
                        QS += "('%s','%s'),"%(com[1],codenum2code[it['f12']])
                stock.execute("insert ignore into emlist (emcode,code) values %s"%QS[:-1])


#打印分类和概念的个股属于flow_em_category
def printemlist():
    companys = xueqiu.get_company_select()
    code2com = xueqiu.get_company_code2com()
    for com in companys:
        if com[3]=='90' or com[3]=='91':
            QS = stock.query("select * from emlist where emcode='%s'"%com[1])
            
            S = ""
            n = 0
            for it in QS:
                if it[1] in code2com:
                    S += "%s,"%it[1]
                    n+=1
            #print(S[:-1])
            print("%s %s %s %d/%d"%(com[1],com[2],com[3],n,len(QS)))


#删除今天的emflow
def deleteEmFlow():
    t = datetime.today()
    n = "emflowts2_%d_%d"%(t.month,t.day)
    k = "emflownp2_%d_%d"%(t.month,t.day)
    shared.delKey(n)
    shared.delKey(k)

"""
检查flow_em_category中的company_id是不是完全和company的id对应
"""
def checkcompanyid():
    qs = stock.query('select company_id,code,name from flow_em_category')
    for it in qs:
        q = stock.query("select id from company where code='%s'"%it[1])
        if len(q)==1:
            if q[0][0]==it[0]:
                continue
            else:
                print("发现id不一致%s"%str(it))

def PopupK(code,period=None,mode='auto'):
    kline.Plote(code,period,config={'index':True},mode=mode).showKline(figsize=(16,10),popup=True)

def get_last_rt(t):
    b,k,d = xueqiu.getTodayRT(t)
    t2 = t
    if not b:
        for i in range(1,7):
            t2 = t-timedelta(days=i)
            b,k,d = xueqiu.getTodayRT(t2)
            if b:
                break
    return t2,k,d

"""
遍历过往概念的1分钟级别的数据
"""
def enumrt(bi,cb,data,param):
    t = bi
    today = datetime.today()
    while t<=today:
        ids,k,d = ziprt.readbydate(t)
        if ids is not None:
            cb(t,ids,k,d,data,param)
        t = t+timedelta(days=1)
"""
测试过往数据看看追涨效果
参数：追涨名次，时间
输出：次日最高和亏损情况
并将结果绘制成图表
"""
def testrise():
    bi = datetime(year=2021,month=4,day=6)
    data = []
    lastprice = None
    #(0 t, 1 id,2 price,3 rate,4 rmax,5 rmin,6 avg,7 dmax,8 dmin) 日期,公司id,买入价格，买入时日增长率，次日最大收益，次日最低收益，次日平均收益，最大收益时间，最小收益时间
    # companys 0 company_id,1 code,2 name,3 prefix
    # k = [(0 price,1 当日涨幅,2 volume,3 larg,4 big,5 mid,6 ting)]
    # k = [(0 price,1 volume,2 hug,3 ting)] 精简
    def cb(t,ids,k,d,data,param):
        nonlocal lastprice
        if len(data)>0: #处理上一个买入的结果数据
            S = data[-1]
            for i in range(len(ids)):
                if ids[i]==S[1]:
                    imax = k[i,15:,0].argmax()+15
                    imin = k[i,15:,0].argmin()+15
                    rmax = (k[i,imax,0]-S[2])/S[2]
                    rmin = (k[i,imin,0]-S[2])/S[2]
                    dmax = d[imax]
                    dmin = d[imin]
                    avg = (np.mean(k[i,:,0])-S[2])/S[2]
                    S[4] = rmax
                    S[5] = rmin
                    S[6] = avg
                    S[7] = dmax
                    S[8] = dmin
                    break
        #下面进入本日追涨买入
        i = 0
        for i in range(len(d)):
            if d[i].hour==9 and d[i].minute>=param:
                break
        R = []
        if lastprice is None:
            lastprice = {}
            for j in range(k.shape[0]):
                lastprice[ids[j]] = k[j,0,0]
        for j in range(k.shape[0]):
            price = k[j,i,0]
            if ids[j] in lastprice:
                r = (price-lastprice[ids[j]])/lastprice[ids[j]]
                flow = k[j,i,2]
                if r>0 and flow>0:
                    R.append((ids[j],price,r))
        R = sorted(R,key=lambda it:it[2],reverse=True)
        S = R[0]
        data.append([t,S[0],S[1],S[2],0,0,0,None,None])
        #将当日的最后一个价格作为收盘价格
        for j in range(k.shape[0]):
            lastprice[ids[j]] = k[j,-1,0]    

    id2com = xueqiu.get_company_select_id2com()
    for param in range(31,35):
        data = []
        enumrt(bi,cb,data,param)
        avgbuy = 0
        avgmax = 0
        avgmin = 0
        avgavg = 0
        for it in data:
            ts = ''
            if it[7] is not None and it[8] is not None:
                ts = "\t%s\t%s"%(stock.timeString2(it[7]),stock.timeString2(it[8]))
            print("%d\t%s\t%s\t%.02f%%\t%.02f%%\t%.02f%%\t%.02f%%\t%s"%(param,str(it[0]),id2com[it[1]][2],100*it[3],100*it[4],100*it[5],100*it[6],ts))
            avgbuy += it[3]
            avgmax += it[4]
            avgmin += it[5]
            avgavg += it[6]
        print(("%d\t%.02f%%\t%.02f%%\t%.02f%%\t%.02f%%")%(param,100*avgbuy/len(data),100*avgmax/len(data),100*avgmin/len(data),100*avgavg/len(data)))

#testrise()
"""
其他都和1一样，增加了9:30-9:40之间的操作，进行追加仓位来扩大收益
"""
def testrise2():
    bi = datetime(year=2021,month=4,day=6)
    data = []
    lastprice = None
    #(0 t, 1 id,2 price,3 rate,4 rmax,5 rmin,6 avg,7 dmax,8 dmin,9 mul) 日期,公司id,买入价格，买入时日增长率，次日最大收益，次日最低收益，次日平均收益，最大收益时间，最小收益时间，持仓乘数
    # companys 0 company_id,1 code,2 name,3 prefix
    # k = [(0 price,1 当日涨幅,2 volume,3 larg,4 big,5 mid,6 ting)]
    # k = [(0 price,1 volume,2 hug,3 ting)] 精简
    def cb(t,ids,k,d,data,param):
        nonlocal lastprice
        if len(data)>0: #处理上一个买入的结果数据
            S = data[-1]
            for i in range(len(ids)):
                if ids[i]==S[1]:
                    imax = k[i,15:,0].argmax()+15
                    imin = k[i,15:,0].argmin()+15
                    rmax = S[9]*(k[i,imax,0]-S[2])/S[2]
                    rmin = S[9]*(k[i,imin,0]-S[2])/S[2]
                    dmax = d[imax]
                    dmin = d[imin]
                    avg = S[9]*(np.mean(k[i,:,0])-S[2])/S[2]
                    S[4] = rmax
                    S[5] = rmin
                    S[6] = avg
                    S[7] = dmax
                    S[8] = dmin
                    break
        #下面进入本日追涨买入
        i30 = 0
        i35 = 0
        i40 = 0
        for i in range(len(d)):
            if d[i].hour==9 and d[i].minute==param:
                i30 = i
            if d[i].hour==9 and d[i].minute==35:
                i35 = i
            if d[i].hour==9 and d[i].minute==40:
                i40 = i
                break
        R = []
        if lastprice is None:
            lastprice = {}
            for j in range(k.shape[0]):
                lastprice[ids[j]] = k[j,0,0]
        for j in range(k.shape[0]):
            if ids[j] in lastprice:
                price30 = k[j,i30,0]
                price35 = k[j,i35,0]
                price40 = k[j,i40,0]
                r = (price30-lastprice[ids[j]])/lastprice[ids[j]]
                flow = k[j,i30,2]
                m = 1 #乘数
                price = price30 #平均成本
                if r>0 and flow>0:
                    """
                    if price35>price30 and k[j,i35,2]>k[j,i30,2]:
                        m += 1
                        price = (price+price35)/2.
                        if price40>price35 and k[j,i40,2]>k[j,i35,2]:
                            m += 1
                            price = price*2./3. + price40/3.
                    """
                    R.append((ids[j],price,r,m))
        R = sorted(R,key=lambda it:it[2],reverse=True)
        if len(R)>0:
            S = R[0]
            data.append([t,S[0],S[1],S[2],0,0,0,None,None,S[3]])
        #将当日的最后一个价格作为收盘价格
        for j in range(k.shape[0]):
            lastprice[ids[j]] = k[j,-1,0]    

    id2com = xueqiu.get_company_select_id2com()
    for param in range(31,32):
        data = []
        enumrt(bi,cb,data,param)
        avgbuy = 0
        avgmax = 0
        avgmin = 0
        avgavg = 0
        for it in data:
            ts = ''
            if it[7] is not None and it[8] is not None:
                ts = "\t%s\t%s"%(stock.timeString2(it[7]),stock.timeString2(it[8]))
            m = it[9]
            #print("%d\t%s\t%s\t%s\t%.02f%%\t%.02f%%\t%.02f%%\t%.02f%%\t%s\t%d"%(param,str(it[0]),id2com[it[1]][1],id2com[it[1]][2],100*it[3],100*it[4],100*it[5],100*it[6],ts,m))
            t = it[0]
            t = datetime(year=it[0].year,month=it[0].month,day=it[0].day,hour=9,minute=30)
            print("K('%s',5,'%s')"%(id2com[it[1]][1],str(t)))
            avgbuy += it[3]
            avgmax += it[4]
            avgmin += it[5]
            avgavg += it[6]
        #print(("%d\t%.02f%%\t%.02f%%\t%.02f%%\t%.02f%%")%(param,100*avgbuy/len(data),100*avgmax/len(data),100*avgmin/len(data),100*avgavg/len(data)))

#testrise2()
"""
def K(code,period,pos):
    kline.Plote(code,period,mode='normal',lastday=2*365).show(figsize=(32,15),pos=pos)
K('BK0450',5,'2021-04-07 09:35:00')
"""

monitor.riseview('2021-06-03',3,40)