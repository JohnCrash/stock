import requests
import time
import math

def xueqiuJson(url):
    s = requests.session()
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
            'Cookie':'_ga=GA1.2.528987204.1555945543; device_id=3977a79bb79f8dd823919ae175048ee6; s=ds12dcnoxk; __utmz=1.1555945599.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); bid=693c9580ce1eeffbf31bb1efd0320f72_jushvajy; aliyungf_tc=AQAAAOIpumBckAMAiQbzchVmEU+Ji7i7; __utmc=1; xq_a_token.sig=71HQ_PXQYeTyQvRDRGXoyAI8Cdg; xq_r_token.sig=QUTS2bLrXGdbA80soO-wu-fOBgY; __utma=1.528987204.1555945543.1571234998.1573824873.28; Hm_lvt_1db88642e346389874251b5a1eded6e3=1574067809; acw_tc=2760822d15749152971941684e7f4320cc69616649eafea22bc5d90f26efbe; remember=1; xq_a_token=6ed8f0f9f30bc4f13f65bb3102333a0ead64c3ca; xqat=6ed8f0f9f30bc4f13f65bb3102333a0ead64c3ca; xq_r_token=aa3abe067eed22f1c36774dec016a669fa845891; xq_is_login=1; u=6625580533; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1575272484; snbim_minify=true'}
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
