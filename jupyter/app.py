from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
   return 'Hello World'

"""
请求k数据
"""
@app.route('/k/<code>/<period>/<args>')
def k(code,period,args):
    return code+'+'+args

if __name__ == '__main__':
   app.run()