"""
d1是k1的日期表,将k1和日期表date对齐
d1和date来自于loadKline的返回日期
"""
import numpy as np
import stock
import status
import shared
import xueqiu
import threading
import queue
import requests
import time
from datetime import datetime,date,timedelta
from IPython.core.interactiveshell import InteractiveShell
import kline
import math
import config
import subprocess
import threading
"""
companys = stock.query("select company_id,code,name,category from company_select")
coms = []
id2com = {}
i = 0
for com in companys:
    coms.append(com[1])
    id2com[com[0]] = com
    if com[1]=='SZ300173':
        print(i)
        print(com)
    i+=1
def progress(i):
    print(i)

status.StrongSortedRT([3],progress=progress,companys=companys)
"""
"""
def progress(i):
    #print(i)
    pass
companys = stock.query("select company_id,code,name,category,ttm,pb from company_select")
id2companys = {}
for c in companys:
    id2companys[c[0]] = c
def isRasing(a,c,istoday):
    #istoday True可以使用xueqiu数据
    #c [0 company_id,1 code,2 name,3 category,4 ttm,5 pb]  
    #0 id ,1 close,2 volume,3 volumema20,4 macd,5 energy,6 volumeJ,7 bollup,8 bollmid,9 bolldn,10 bollw
    print("%s %s [vol=%f万,vol=%f万,close=%f,energy=%f,macd=%f]"%(c[1],c[2],round(a[-2,2]/10000,2),round(a[-1,2]/10000,2),a[-1,1],a[-1,5],a[-1,4]))
    dMACD = a[-1,4]-a[-2,4]
    #macd在零轴附件（预计2日穿过或者已经穿过2日）,股价涨,能量线崛起
    if dMACD>0 and a[-1,1]-a[-2,1]>0 and a[-1,5]>=3 and a[-2,5]<3:
        if (a[-1,4]<0 and a[-1,4]+2*dMACD>0) or (a[-1,4]>0 and a[-1,4]-2*dMACD<0):
            return True,[{'x':[-1],'color':'magenta','linestyle':'--','linewidth':2}]
    return False,[]    
rasing,vlines = status.searchRasingCompanyStatusByRT('2020-06-05','d',isRasing,id2companys,progress)    
"""
#xueqiu.clearAllRT()
#status.updateRT(companys)

#xueqiu.sinaFlowRT()
#print('Done')
#status.saveflow()
"""
def process(i):
    pass
print("保存资金流向到数据库...")
xueqiu.sinaFlowRT()
status.saveflow()
print("开始更新数据库...")
status.update_status(process)
print("更新完成。") 
"""

'''
#status.showzdt(bi='2019-01-02',ei='2019-10-01')
companys = stock.query("""select company_id,code,name,category,ttm,pb from company_select""")
id2companys = {}
for c in companys:
    id2companys[c[0]] = c
def process(i):
    pass
def myfilter(a,c,istoday):
    #istoday True可以使用xueqiu数据
    #c [0 company_id,1 code,2 name,3 category,4 ttm,5 pb]  
    #0 id ,1 close,2 volume,3 volumema20,4 macd,5 energy,6 volumeJ,7 bollup,8 bollmid,9 bolldn,10 bollw
    dMACD = a[-1,4]-a[-2,4]
    #macd在零轴附件（预计2日穿过或者已经穿过2日）,股价涨,能量线崛起
    if dMACD>0 and a[-1,1]-a[-2,1]>0 and a[-1,5]>=3 and a[-2,5]<3:
        if (a[-1,4]<0 and a[-1,4]+2*dMACD>0) or (a[-1,4]>0 and a[-1,4]-2*dMACD<0):
            return True,[{'x':[-1],'color':'magenta','linestyle':'--','linewidth':2}]
    return False,[]
rasing_ids,vlines = status.searchRasingCompanyStatusByRT_test('2020-04-30','d',myfilter,id2companys,process)
cl = {}
for v in rasing_ids:
    c = id2companys[v]
    if c[3] not in cl:
        cl[c[3]] = []
    cl[c[3]].append(c)
print('崛起数量:',len(rasing_ids))
for k in cl:
    print(k,'\t',len(cl[k]))
    for c in cl[k]:
        print('\t',c)
'''
#xueqiu.sinaFlowRT()
#status.saveflow() 
#subprocess.run(['d:/test.bat'])
#print('DONE!')

#b,k = xueqiu.xueqiuK('SZ399001',5,96)
#print(k)
"""
r = status.search(status.cb_rsi_left_buy)
for k in r:
    print(k,' ',len(r[k]))
    for c in r[k]:
        print('\t',c)
"""        
"""
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
"""        
#2020-5-24 18:30 产生的cookie
#过期 2020-05-24 18:33:23
#看看此cookie什么时候过期

#config.xueqiu_cookie = "u=181590314603123; xq_a_token=328f8bbf7903261db206d83de7b85c58e4486dda; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTU5MTg0Mjc0NiwiY3RtIjoxNTkwMzE0NTcyMTc2LCJjaWQiOiJkOWQwbjRBWnVwIn0.hYulk1CAui6ZwGsAWT1-UNsExLyGpL-932q-EOvHmD4xWD6PZ8PEFwR1AvV1EJF2qpTmbgJARCP4pYEaov6_q32tOfdMogouuC42S6VSXRH8_kij1ZJ5Czo2_5obrnGRAfSopgbqXtQryGVnq7AuaU8hRhpHOHaHKAs6WsHYRYFpKzM8oou_QcGjmf9aRjfoh8B08ANa8qe6I_jc9Alase6E14nMuBkYVIv3ZERRNjV6g-32aO8og_wDmUnbIInG_qgtmrdDh8jf1yrnHpM6yj-oI0F5Cd1V77nhRiyHuwk1zxIHMkJsN_sNcyExb0-w8J7ru1V2sBLiXl6SBuGh3g; xq_r_token=22ab4927b9acb2a02a4efefe14ccbbc589e007cb; xqat=328f8bbf7903261db206d83de7b85c58e4486dda; acw_tc=2760825015903146031176766e4babd51f2c70e7d445cc809b41e549210145; aliyungf_tc=AQAAAJn5gzfUtwEA4PCD3pBqgWAE3771"
#config.xueqiu_cookie = "_ga=GA1.2.528987204.1555945543; xq_a_token.sig=71HQ_PXQYeTyQvRDRGXoyAI8Cdg; xq_r_token.sig=QUTS2bLrXGdbA80soO-wu-fOBgY; snbim_minify=true; device_id=c8a242cd517399e92fd6562fe3c117c8; s=cx12eqso7r; bid=693c9580ce1eeffbf31bb1efd0320f72_k9ifcem7; Hm_lvt_1db88642e346389874251b5a1eded6e3=1588479908,1588497324,1588500208,1588725333; remember=1; xq_a_token=5e8099ac0db1c598a4f5a6e387ce8b475b55907d; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOjY2MjU1ODA1MzMsImlzcyI6InVjIiwiZXhwIjoxNTkxMzE5NTQ5LCJjdG0iOjE1ODg3Mjc1NDk3NjAsImNpZCI6ImQ5ZDBuNEFadXAifQ.BxX9yHSOGmay23lKFDds6HCph2yoDFNbakT-KXDIcVf9-RdY-nSdTHwecvJIx5GeUKqL0yQACue8E7rdb_mWu2srL21IB-A38q2mXdQldd6hFlMnCf_YC1nmKy-D9VeWcG0i1kBdMxN_FJU5Ec9gq9Kz8skKd0KkIzmEpKVTo7TXpdH3KGUYEi30Peo8byzLGr1-jfI6cFDZOH2Ari5xcftDyKX1m6katCCVhax2WBvnVyVstgdR6ARDcXobYj8TUgA04ad87-MzHUN9hxWDFG2DnUW71JkSJylD6AKj08Uel7fG5Z8RohLpTTPf3xI0PVjtkzW4QDVIbpPuQlf8yQ; xqat=5e8099ac0db1c598a4f5a6e387ce8b475b55907d; xq_r_token=7d0878951d8ea7e00bba60070b2f3616df9c6198; xq_is_login=1; u=6625580533; is_overseas=0; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1588727553"
#b,c = xueqiu.xueqiuCookie()
#b,k = xueqiu.xueqiuK('SZ399001',5,96)
#print(b,k)

#c,k,d = stock.loadKline("SH000001",5)
#k15,d15 = stock.mergeK(k,d,3)
#print(k15)

shared.delKey("SH688012")
