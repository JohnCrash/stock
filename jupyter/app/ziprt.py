import pickle
from subprocess import list2cmdline
import zlib
import os
import numpy as np
from datetime import date,datetime,timedelta

from numpy.core.fromnumeric import compress
from . import xueqiu
from . import config
"""
判断文件是否存在，存在返回True,否则返回False
"""
def isexist(name):
    try:
        s = os.stat(name)
        return s.st_size>0
    except Exception as e:
        return False

"""
将[company_id,...],k,d,[盘价,...]
"""
def compressRT(ids,k,d):
    info = pickle.dumps([k.shape,k.dtype.name,ids,d])
    length = int(len(info))
    encoded = length.to_bytes(2,byteorder='big')+info+k.tobytes()
    return zlib.compress(encoded)

"""
返回[company_id,...],k,d,[开盘,..]
"""
def decompressRT(data):
    encoded = zlib.decompress(data)
    length = int.from_bytes(encoded[:2],byteorder='big')
    info = pickle.loads(encoded[2:2+length])
    a = np.frombuffer(encoded,dtype=info[1],offset=2+length).reshape(info[0])
    return info[2],a,info[3]

def readRT(name):
    try:
        with open(name,'rb') as f:
            ids,k,d = decompressRT(f.read())
            return ids,k,d
    except FileNotFoundError as e:
        pass
    return None,None,None

def writeRT(name,ids,k,d):
    with open(name,'wb') as f:
        f.write(compressRT(ids,k,d))

def readbydate(t):
    name = '%s%d%02d%02d.rt'%(config.zipdir,t.year,t.month,t.day)
    return readRT(name)
"""
将rt数据存入到文件中去
"""
def saveRT():
    t = datetime.today()
    companys = xueqiu.get_company_select()
    ids = []
    ss = np.zeros((len(companys),),dtype=np.dtype('bool'))
    for i in range(len(companys)):
        com = companys[i]
        if com[3]=='90' or com[3]=='91' or com[1]=='SZ399001' or com[1]=='SH000001':
            ids.append(com[0])
            ss[i] = True
    
    for i in range(0,7):
        b,k,d = xueqiu.getTodayRT(t-timedelta(days=i))
        if b:
            ct = d[-1]
            if ct.hour==15 or (ct.hour==14 and ct.minute>=58):
                name = '%s%d%02d%02d.rt'%(config.zipdir,ct.year,ct.month,ct.day)
                if not isexist(name):
                    """
                    数据仅仅保存主力和小单
                    """
                    if len(ss)==k.shape[0]:
                        K = np.zeros((len(ids),k.shape[1],k.shape[2]-3))
                        K[:,:,0] = k[ss,:,0]
                        K[:,:,1] = k[ss,:,2]
                        K[:,:,2] = k[ss,:,3]+k[ss,:,4]
                        K[:,:,3] = k[ss,:,6]
                    else:
                        ss1 = ss[:k.shape[0]]
                        K = np.zeros((np.count_nonzero(ss1),k.shape[1],k.shape[2]-3))
                        K[:,:,0] = k[ss1,:,0]
                        K[:,:,1] = k[ss1,:,2]
                        K[:,:,2] = k[ss1,:,3]+k[ss1,:,4]
                        K[:,:,3] = k[ss1,:,6]
                    writeRT(name,ids,K,d)
        #存储955
        b,k,d,ls = xueqiu.getEmflowRT9355()
        if b:
            name = '%s%d%02d%02d.955'%(config.zipdir,ct.year,ct.month,ct.day)
            if not isexist(name):
                """
                数据仅仅保存主力和小单
                """
                K = np.zeros((len(ls),k.shape[1],k.shape[2]-3))
                K[:,:,0] = k[ss,:,0]
                K[:,:,1] = k[ss,:,2]
                K[:,:,2] = k[ss,:,3]+k[ss,:,4]
                K[:,:,3] = k[ss,:,6]

                writeRT(name,ls,K,d)            

"""
将北向数据存入压缩保存
"""
def bxzj2db():
    t = datetime.today()
    if t.hour>=15:
        for i in range(5):
            b,j = xueqiu.bxzj()
            if b and 'data' in j and 's2n' in j['data']:
                data = j['data']['s2n']
                if len(data)>=240 and len(data[-1])>12:
                    datazip = zlib.compress(pickle.dumps(data))
                    name = '%sbxzj%d%02d%02d'%(config.zipdir,t.year,t.month,t.day)
                    with open(name,'wb') as f:
                        f.write(datazip)
                    return
                else:
                    print('bxzj2db 数据不完整')
                    return
        print('bxzj2db 没有成功下载')
