"""
对所有股票进行计算
计算器日macd，周macd，日能量，周能量，日成交量kdJ,周成交量kdJ
算法是增量优化的，每次运行仅仅计算增加的部分
"""
import numpy as np
import stock

def insert_company_status(k,vma20,energy,volumeJ,idd):
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
    print('insert',k[0][0])
    stock.execute("insert ignore into company_status values %s"%(qs))

def update_company_status(idk,idd):
    k = np.array(idk)
    vma20 = stock.ma(k[:,1],20)
    energy = stock.kdj(stock.volumeEnergy(k[:,1]))[:,2]
    volumeJ = stock.kdj(k[:,1])[:,2]

    insert_company_status(k,vma20,energy,volumeJ,idd)

def update_all_status():
    rs = stock.query("""select id,date,volume,close,macd from kd_xueqiu where date>'2010-1-2'""")
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
    for key in idk:
        update_company_status(idk[key],idd[key])
    stock.closedb()
    print('全部更新完成',len(rs))

def update_status():
    stock.opendb()
    stock.query('select date from kd_xueqiu where id=8828 order by date desc limit 1')
    stock.closedb()