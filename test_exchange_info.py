from binance.spot import Spot

client = Spot()

try:
    info = client.exchange_info()
    print("Connected successfully!")
    print(f"Number of symbols: {len(info['symbols'])}")
except Exception as e:
    print(e)