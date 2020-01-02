import requests
import time
import math

def xueqiuJson(url):
    s = requests.session()
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
            'Cookie':'_ga=GA1.2.528987204.1555945543; device_id=3977a79bb79f8dd823919ae175048ee6; s=ds12dcnoxk; __utmz=1.1555945599.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); bid=693c9580ce1eeffbf31bb1efd0320f72_jushvajy; aliyungf_tc=AQAAAOIpumBckAMAiQbzchVmEU+Ji7i7; __utmc=1; xq_a_token.sig=71HQ_PXQYeTyQvRDRGXoyAI8Cdg; xq_r_token.sig=QUTS2bLrXGdbA80soO-wu-fOBgY; snbim_minify=true; acw_tc=2760822d15756229262972757e6f293b44f4b01eff4ceb7a180f0a4c9ed067; Hm_lvt_1db88642e346389874251b5a1eded6e3=1577774083,1577774182,1577774249,1577774257; __utma=1.528987204.1555945543.1577775593.1577826553.72; remember=1; xq_a_token=c44d723738529eb6b274022a320258d92f31cc1e; xqat=c44d723738529eb6b274022a320258d92f31cc1e; xq_r_token=b926ebba0cf9dcf8c01a628b525f93191a24ca0d; xq_is_login=1; u=6625580533; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1577924260'}
    r = s.get(url,headers=headers)
    if r.status_code==200:
        return True,r.json()
    else:
        print(url,r.status_code,r.reason)
        return False,r.reason

def xueqiuK15(code):
    timestamp = math.floor(time.time()*1000)
    uri = """https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=%s&begin=%s&period=15m&type=before&count=-32&indicator=kline"""%(code,timestamp)
    return xueqiuJson(uri)
