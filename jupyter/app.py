import json
from flask import Flask
from app import stock
app = Flask(__name__)

@app.route('/')
def hello_world():
   return 'Hello World'

"""
请求k数据
"""
@app.route('/k/<code>/<period>/<args>')
def k(code,period,args):
   c,k,d = stock.loadKline(code,period)
   dd = []
   for v in d:
      dd.append(stock.dateString(v[0]))
   return json.dumps({'company':json.dumps(c),'k':[],'d':dd})

if __name__ == '__main__':
   app.run()