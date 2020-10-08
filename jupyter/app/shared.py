"""
使用redis在多个python间共享数据
"""
import redis
import numpy as np
import pickle

pool = redis.ConnectionPool(host='localhost', port=6379) #, decode_responses=True

def numpyToRedis(a,n,ex=None):
   """Store given Numpy array 'a' in Redis under key 'n'"""
   global pool
   r = redis.Redis(connection_pool=pool)

   info = pickle.dumps([a.shape,a.dtype.name])
   length = int(len(info))
   encoded = length.to_bytes(2,byteorder='big')+info+a.tobytes()

   # Store encoded data in Redis
   r.set(n,encoded,ex=ex)
   return

def delKey(n):
   global pool
   r = redis.Redis(connection_pool=pool)
   r.delete(n)

def numpyFromRedis(n):
   """Retrieve Numpy array from Redis key 'n'"""
   global pool
   r = redis.Redis(connection_pool=pool)
   encoded = r.get(n)
   if encoded is None:
       return False,None
   length = int.from_bytes(encoded[:2],byteorder='big')
   info = pickle.loads(encoded[2:2+length])
   a = np.frombuffer(encoded,dtype=info[1],offset=2+length).reshape(info[0])
   return True,a

def toRedis(o,n,ex=None):
   global pool
   r = redis.Redis(connection_pool=pool)
   r.set(n,pickle.dumps(o),ex=ex)

def fromRedis(n):
    global pool
    r = redis.Redis(connection_pool=pool)
    encoded = r.get(n)
    if encoded is None:
        return False,None
    return True,pickle.loads(encoded)