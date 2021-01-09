from . import stock
from . import xueqiu
from . import status
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import Formatter
import math

class MyFormatter(Formatter):
    def __init__(self, dates, fmt='%Y-%m-%d'):
        self.dates = dates
        self.fmt = fmt

    def __call__(self, x, pos=0):
        'Return the label for time x at position pos'
        ind = int(np.round(x))
        if ind >= len(self.dates) or ind < 0 or math.ceil(x)!=math.floor(x):
            return ''
        t = self.dates[ind][0]
        return '%s-%s-%s'%(t.year,t.month,t.day)

def calcCatgoryVolumeEnergy(cat):
    companys = stock.query("""select * from company where category='%s'"""%(cat))
    if len(companys)==0:#分类下没有公司
        print('此分类下没有公司:',cat)
    _,sz_k,sz_date = stock.loadKline('SZ:399001',expire=3600) #和深圳成指对齐
    K = sz_k[-400:]
    D = sz_date[-400:]
    KS = np.zeros((len(companys),len(K),5))
    i = 0
    for c in companys:
        c,k,d = stock.loadKline(c[1],after=stock.dateString(D[-400][0]))
        KS[i] = stock.alignK(D,k,d)
        i+=1
    volume = np.zeros((len(K)))
    for i in range(len(K)):
        volume[i] = KS[:,i,0].sum()
    
    return volume,stock.volumeEnergy(volume,20)
"""
对分类的能量线进行
"""
def CatgoryVolumeEnergyPlote():
    cats = stock.query("""select id,name from category""")
    i = 0
    _,sz_k,sz_d = stock.loadKline('SZ399001',expire=3600)
    K = sz_k[-400:]
    D = sz_d[-400:]
    sz_energy = stock.volumeEnergyK(K)
    sz_energy_kdj = stock.kdj(sz_energy)
    for c in cats:
        if status.isPopularCategory(c[1]):
            fig, axs = plt.subplots(1, 1,sharex=True,figsize=(32,5))
            axs.xaxis.set_major_formatter(MyFormatter(D))    
            volume,ve20 = calcCatgoryVolumeEnergy(c[0])
            x = np.arange(len(ve20))
            kdJ = stock.kdj(ve20)
            volumeJ = stock.kdj(volume)
            axs.plot(x[-200:],kdJ[-200:,2],label=c[1])
            axs.plot(x[-200:],volumeJ[-200:,2],color='gray',linestyle='-.')

            axs.plot(x[-200:],sz_energy_kdj[-200:,2],label='深证成指')
            axs.axhline(0,color='green',linestyle='-.')
            axs.axhline(100,color='red',linestyle='-.')
            i += 1
            axs.legend()

#计算分类的5分钟指数k，并将其存入到k5_category
#每次接上一次时间结尾向后计算
def calcCategoryIndex5():
    #使用银行的id来取得最后的更新时间
    lastday = stock.query('select timestamp from k5_category where id=3386 order by timestamp desc limit 1')
    if len(lastday)>0:
        lastday = stock.timeString(lastday[0][0])
    else:
        lastday = '2019-11-01 00:00:00'
    companys = xueqiu.get_company_select()
    #使用上证指数的时间5分钟时间序列
    _,_,D = stock.loadKline('SH000001',5,after=lastday)
    if len(D)==0:
        return #没有新的数据
    K = np.ones((len(companys),len(D),5)) #volume,open,high,low,close
    #转载全部数据
    for i in range(len(companys)):
        com = companys[i]
        _,k,d = stock.loadKline(com[1],5,after=lastday)
        if len(D)==len(d): #日期完整对应
            K[i,:,:] = k 
        elif len(d)>0 and len(D)>len(d): #日期不对应
            J=0
            if d[0][0]<D[0][0]:
                for j in range(len(d)):
                    if d[j][0]>=D[0][0]:
                        J = j
                        break
            for j in range(len(D)):
                if J<len(d) and D[j][0]==d[J][0]:
                    K[i,j,:] = k[J,:]
                    J+=1
        else:
            pass #个股日期不可能多于指数
    csector = xueqiu.get_category_selector()
    name2category = xueqiu.get_category_name2category()
    tv = xueqiu.get_volume_slice('2020-11-02')
    for n in csector:
        r = csector[n]
        N = np.count_nonzero(r)
        if N<=0:
            N = 1
        #计算板块指数
        S = np.sum(K[r,:,0:1],axis=0) #分类中股票的某天成交量累加在一起形成一个向量[len(D)]
        V = np.sum(tv[r,1]) #行业总市值
        X = K[r,:,1:]*(tv[r,1]/V).reshape(N,1,1) #股票的open,high,low,close乘以股票在行业中的权重
        Y = X/tv[r,0].reshape(N,1,1) #然后除以股票在特定点的价格(归一化)
        CK = np.sum(Y,axis=0) #将股票的价格open,high,low,close乘以自己成交量在分类中的权重
        #存储板块指数
        if n in name2category:
            id = name2category[n][0]
            qs = ""
            for i in range(len(D)):
                try:
                    qs += """(%d,'%s',%f,%f,%f,%f,%f),"""%(id,stock.timeString(D[i][0]),S[i][0],CK[i,0],CK[i,1],CK[i,2],CK[i,3])
                except Exception as e:
                    print(e)
                if len(qs)/1024 > 256: #每次插入256k
                    stock.execute("insert ignore into k5_category values %s"%(qs[:-1]))
                    qs = ""
            if len(qs)>0:
                stock.execute("insert ignore into k5_category values %s"%(qs[:-1]))