"""
对所有股票进行计算
计算器日macd，周macd，日能量，周能量，日成交量kdJ,周成交量kdJ
算法是增量优化的，每次运行仅仅计算增加的部分
"""
import numpy as np
import stock
from datetime import date

PROD = 40
#见数据插入到company_status表
def insert_company_status(k,vma20,energy,volumeJ,idd):
    if len(k)>0:
        qs = ""
        for i in range(len(k)):
            #id , date , close , volume , volumema20 , macd , energy , voluemJ
            try:
                macd = 0 if k[i][3] is None else k[i][3]
                if i!=len(k)-1:
                    qs+="""(%d,'%s',%f,%f,%f,%f,%f,%f),"""%(k[i][0],stock.dateString(idd[i]),k[i][2],k[i][1],vma20[i],macd,energy[i],volumeJ[i])
                else:
                    qs+="""(%d,'%s',%f,%f,%f,%f,%f,%f)"""%(k[i][0],stock.dateString(idd[i]),k[i][2],k[i][1],vma20[i],macd,energy[i],volumeJ[i])
            except Exception as e:
                print(e)
                print(k[i])
                print(idd[i])
        
        stock.execute("insert ignore into company_status values %s"%(qs))

#依据完整数据更新
def update_company_status_all_data(idk,idd):
    k = np.array(idk)
    vma20 = stock.ma(k[:,1],20)
    energy = stock.kdj(stock.volumeEnergy(k[:,1]))[:,2]
    volumeJ = stock.kdj(k[:,1])[:,2]

    insert_company_status(k,vma20,energy,volumeJ,idd)

#依据增量数据更新
def update_company_status_delta_data(idk,idd):
    k = np.array(idk)
    vma20 = stock.ma(k[:,1],20)
    energy = stock.kdj(stock.volumeEnergy(k[:,1]))[:,2]
    volumeJ = stock.kdj(k[:,1])[:,2]

    insert_company_status(k[PROD+1:],vma20[PROD+1:],energy[PROD+1:],volumeJ[PROD+1:],idd[PROD+1:])

#可以从一个起点日期使用增量进行更新，或者更新全部数据
def update_status_begin(beginday,isall=False):
    if isall:
        rs = stock.query("""select id,date,volume,close,macd from kd_xueqiu where date>'%s'"""%(beginday))
    else:
        #需要提前20个交易日的数据
        lastdays = stock.query("select date from kd_xueqiu where id=8828 and date>'2019-11-01' order by date desc")
      
        #从beginday前面在增加20个交易日
        for i in range(len(lastdays)):
            if lastdays[i][0] == beginday:
                lastday = lastdays[i+PROD][0]
                break

        rs = stock.query("""select id,date,volume,close,macd from kd_xueqiu where date>='%s'"""%(lastday))
    idk = {}
    idd = {}
    for i in range(len(rs)):
        d = rs[i]
        key = d[0]
        if key not in idk:
            idk[key] = []
            idd[key] = []
        #0 id,1 volume,2 close,3 macd
        idk[key].append([rs[i][0],rs[i][2],rs[i][3],rs[i][4]])
        idd[key].append(rs[i][1])

    if isall:
        for key in idk:
            update_company_status_all_data(idk[key],idd[key])
    else:
        for key in idk:
            update_company_status_delta_data(idk[key],idd[key])

#更新company_status表
def update_status():
    lastday = stock.query('select date from company_status where id=8828 order by date desc limit 1')
    if len(lastday)==1:
        if lastday[0][0] != date.today():
            update_status_begin(lastday[0][0])
    else:
        update_status_begin('2010-1-2',True)
    stock.closedb()

update_status()