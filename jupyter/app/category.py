from . import stock
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