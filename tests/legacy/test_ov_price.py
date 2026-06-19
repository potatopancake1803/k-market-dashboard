import sys
sys.path.append('api_documents/KIS_github/open-trading-api')
from examples_llm.overseas_stock.price.price import price
import yaml

with open('api_documents/KIS_github/open-trading-api/kis_devlp.yaml') as f:
    config = yaml.safe_load(f)
ak = config['APP_KEY']
sk = config['APP_SECRET']

import requests
r = requests.post('https://openapi.koreainvestment.com:9443/oauth2/tokenP', json={'grant_type': 'client_credentials', 'appkey': ak, 'appsecret': sk})
tok = r.json()['access_token']

df = price(tok, "NAS", "AAPL", env_dv="real")
if df is not None and not df.empty:
    for col in df.columns:
        print(f"{col}: {df.iloc[0][col]}")
