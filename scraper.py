import requests
import os
import re 
import warnings
import json
warnings.filterwarnings("ignore", message="Unverified HTTPS request")
session = requests.Session()
session.verify = False


def getData(payload):

    headers = {
        'Host': 'www.turkiye.gov.tr',
        # 'Content-Length': '156',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Sec-Ch-Ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        'Sec-Ch-Ua-Platform': '"macOS"',
        'Dnt': '1',
        'Sec-Ch-Ua-Mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': '*/*',
        'Origin': 'https://www.turkiye.gov.tr',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://www.turkiye.gov.tr/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama',
        # 'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9,tr-TR;q=0.8,tr;q=0.7,da;q=0.6,so;q=0.5,hu;q=0.4,ru;q=0.3',
        'Connection': 'close',
        # 'Cookie': 'language=tr_TR.UTF-8; _uid=1674259827-2f095cbb-e381-4e10-9103-5808fbdea03a; w3p=4073957568.20480.0000; w3a=10001862-b949d64-4332812da-f1906565-9285-4079-92f3-e0d8a771ce61; TURKIYESESSIONID=hb2fs79bq9q3u6rv8acl7s0qlg; TS01ee3a52=015c1cbb6da51da576c129aba01d61353c0d0156df6f98c9a12fb11cb658f928b44029c9079f6df12408101dc49f771f903de01bd2ecda9e88c89316cebef4e678611428c4c1262466f577e4525e635e2aee28a91e; _lastpts=1675769913',
    }

    data = f"token={os.environ['token']}&ajax=1&pn=/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama&{payload}"

    res = session.post(
        'https://www.turkiye.gov.tr/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama?submit',
        headers=headers,
        data=data,
    )
    if res.headers['Content-Type'].startswith('application/json'):
        return res
    else:
        getToken()
        return getData(payload)
def getToken():

    headers = {
        'Host': 'www.turkiye.gov.tr',
        'Cache-Control': 'max-age=0',
        'Sec-Ch-Ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"macOS"',
        'Dnt': '1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        # 'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9,tr-TR;q=0.8,tr;q=0.7,da;q=0.6,so;q=0.5,hu;q=0.4,ru;q=0.3',
        'Connection': 'close',
    }

    response = session.get(
        'https://www.turkiye.gov.tr/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama',
        headers=headers,
    )
    return re.search(r'data-token=\"([^"]*)\"', response.text).group(1)

def queryPoint(lat,lng):
    headers = {
    'Host': 'www.turkiye.gov.tr',
    # 'Content-Length': '207',
    'Sec-Ch-Ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
    'Dnt': '1',
    'Sec-Ch-Ua-Mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest',
    'Sec-Ch-Ua-Platform': '"macOS"',
    'Origin': 'https://www.turkiye.gov.tr',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://www.turkiye.gov.tr/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama?harita=goster',
    # 'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,tr-TR;q=0.8,tr;q=0.7,da;q=0.6,so;q=0.5,hu;q=0.4,ru;q=0.3',
    'Connection': 'close',
    # 'Cookie': 'language=tr_TR.UTF-8; _uid=1674259827-2f095cbb-e381-4e10-9103-5808fbdea03a; w3p=4073957568.20480.0000; TURKIYESESSIONID=81klgq8s9dsaj74n3bocjujk6q; TS01ee3a52=015c1cbb6d40f9965902ae7001ac6a406e56593966cf2a57234dfdc8047f1da93ef2de93ee0c0c2e52dc7cf03c8f156fb5ac18977adcbf922efcc469c8634e50a117e0bd7fcf17e4bdc35ae25ff3c0b5744ced0f1b395badece1177ab9097ea01c325eb707; _lastpts=1675786612',
    }

    data = {
        'pn': '/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama',
        'ajax': '1',
        'token': os.environ['token'],
        'islem': 'getAlanlarForNokta',
        'lat': lat,
        'lng': lng,
    }

    response = session.post(
        'https://www.turkiye.gov.tr/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama?harita=goster&submit',
        headers=headers,
        data=data,
    )
    return response.json()


def getFromMap(ilKodu, ilceKodu, mahalleKodu):
    headers = {
    'Host': 'www.turkiye.gov.tr',
    # 'Content-Length': '137',
    'Cache-Control': 'max-age=0',
    'Sec-Ch-Ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"macOS"',
    'Origin': 'https://www.turkiye.gov.tr',
    'Dnt': '1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Referer': 'https://www.turkiye.gov.tr/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama',
    # 'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,tr-TR;q=0.8,tr;q=0.7,da;q=0.6,so;q=0.5,hu;q=0.4,ru;q=0.3',
    'Connection': 'close',
    }
    data = {
        'ilKodu': ilKodu,
        'ilceKodu': ilceKodu,
        'mahalleKodu': mahalleKodu,
        'sokakKodu': '',
        'token': os.environ['token'],
        'btn': 'Sorgula',
    }
    res = session.post(
        'https://www.turkiye.gov.tr/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama?submit',
        headers=headers,
        data=data,
    )
    reRes = re.search(r'toplanmaAlanlari = (.*);', res.text).group(1)
    if reRes == 'null':
        return None

    queries = vertices(json.loads(reRes)[0]['geometry']['coordinates'])
    queryResults = []
    for q in queries:
        qR = queryPoint(q[0], q[1])
        while qR is None:
            getToken()
            qR = queryPoint(q[0], q[1])
        for qRi in qR['features']:
            queryResults.append(qRi)
    return queryResults


def vertices(polygon):
    process = polygon[0]
    if len(process) < 6:
        return process
    res = []
    process.sort(key=lambda x: x[0])
    res.append(process[0])
    process.sort(key=lambda x: x[1])
    res.append(process[0])
    process.sort(key=lambda x: x[0], reverse=True)
    res.append(process[0])
    process.sort(key=lambda x: x[1], reverse=True)
    res.append(process[0])

    avg1 = sum([x[0] for x in res]) / 4
    avg2 = sum([x[1] for x in res]) / 4
    res.append([avg1, avg2])
    return res


def __init__():
    os.environ['token'] = getToken()
    
if '__main__' == __name__:
    __init__()