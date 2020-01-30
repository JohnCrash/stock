"""
使用redis在多个python间共享数据
"""
import struct
import redis
import numpy as np
import pickle

pool = redis.ConnectionPool(host='localhost', port=6379) #, decode_responses=True

def numpyToRedis(a,n,ex=None):
   """Store given Numpy array 'a' in Redis under key 'n'"""
   global pool
   r = redis.Redis(connection_pool=pool)
   w = 0
   z = 0
   if len(a.shape)==1:
      h = a.shape[0]
   elif len(a.shape)==2:
      h, w = a.shape
   else:
      h, w, z = a.shape
   shape = struct.pack('>III',h,w,z)
   encoded = shape + a.tobytes()

   # Store encoded data in Redis
   r.set(n,encoded,ex=ex)
   r.set(n+'_type',a.dtype.name,ex=ex)
   return

def delKey(n):
   global pool
   r = redis.Redis(connection_pool=pool)
   r.delete(n)
   r.delete(n+'_type')

def numpyFromRedis(n):
   """Retrieve Numpy array from Redis key 'n'"""
   global pool
   r = redis.Redis(connection_pool=pool)
   encoded = r.get(n)
   if encoded is None:
       return False,None
   h, w , z = struct.unpack('>III',encoded[:12])
   tp = r.get(n+'_type')
   if w==0:
      a = np.frombuffer(encoded, dtype=tp,offset=12).reshape(h)
   elif z==0:
      a = np.frombuffer(encoded, dtype=tp,offset=12).reshape(h,w)
   else:
      a = np.frombuffer(encoded, dtype=tp,offset=12).reshape(h,w,z)
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