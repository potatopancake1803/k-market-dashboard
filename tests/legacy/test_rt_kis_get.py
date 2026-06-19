import sys
import json
import unittest.mock

# mock plotly
sys.modules['plotly'] = unittest.mock.MagicMock()
sys.modules['plotly.graph_objects'] = unittest.mock.MagicMock()

sys.path.append('scripts')
import market_dashboard3_realtime as m

print("testing HHDFS00000300...")
j = m._rt_kis_get("/uapi/overseas-price/v1/quotations/price", "HHDFS00000300", {"AUTH": "", "EXCD": "NAS", "SYMB": "AAPL"})
print(json.dumps(j, indent=2))
