import requests, json

def test():
    with open('/Users/minjun1803/Documents/Python/Project_Market_Dashboard/scripts/한국투자증권/API_Key_한국투자증권.env') as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
    ak = lines[0].split('=')[1].strip()
    sk = lines[1].split('=')[1].strip()
    
    print(f"AK: {ak[:5]}... SK: {sk[:5]}...")
    r = requests.post('https://openapi.koreainvestment.com:9443/oauth2/tokenP', json={'grant_type': 'client_credentials', 'appkey': ak, 'appsecret': sk})
    tok = r.json().get('access_token')
    if not tok: return print("token error", r.text)

    r2 = requests.get(
        'https://openapi.koreainvestment.com:9443/uapi/overseas-price/v1/quotations/price',
        headers={'authorization': f'Bearer {tok}', 'appkey': ak, 'appsecret': sk, 'tr_id': 'HHDFS00000300'},
        params={'AUTH': '', 'EXCD': 'NAS', 'SYMB': 'AAPL'}
    )
    o = r2.json().get('output', {})
    print("HHDFS00000300:", json.dumps(o, indent=2))
test()
