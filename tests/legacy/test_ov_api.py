import requests
import json

def test():
    ak = None
    sk = None
    with open('/Users/minjun1803/Documents/Python/Project_Market_Dashboard/.env', 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            if 'APP_KEY' in line:
                ak = line.split('=')[1].strip('"\' ')
            elif 'APP_SECRET' in line:
                sk = line.split('=')[1].strip('"\' ')
            elif '=' not in line:
                if not ak: ak = line
                elif not sk: sk = line

    print(f"AK: {ak[:5]}...")
    r = requests.post('https://openapi.koreainvestment.com:9443/oauth2/tokenP', json={'grant_type': 'client_credentials', 'appkey': ak, 'appsecret': sk})
    tok = r.json().get('access_token')
    if not tok:
        print("token error:", r.text)
        return
    
    r2 = requests.get(
        'https://openapi.koreainvestment.com:9443/uapi/overseas-price/v1/quotations/price',
        headers={'authorization': f'Bearer {tok}', 'appkey': ak, 'appsecret': sk, 'tr_id': 'HHDFS00000300'},
        params={'AUTH': '', 'EXCD': 'NAS', 'SYMB': 'AAPL'}
    )
    print("HHDFS00000300:", json.dumps(r2.json(), indent=2))

    r3 = requests.get(
        'https://openapi.koreainvestment.com:9443/uapi/overseas-price/v1/quotations/price-detail',
        headers={'authorization': f'Bearer {tok}', 'appkey': ak, 'appsecret': sk, 'tr_id': 'HHDFS76200200'},
        params={'AUTH': '', 'EXCD': 'NAS', 'SYMB': 'AAPL'}
    )
    print("HHDFS76200200:", json.dumps(r3.json(), indent=2))
test()
