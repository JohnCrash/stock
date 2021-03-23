import numpy as np
import requests
import time
from datetime import date,datetime,timedelta
import json
from . import mylog
from . import config
from . import shared
from . import xueqiu
from . import stock

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

