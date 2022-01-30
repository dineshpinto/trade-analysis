import pandas as pd
import yaml
from dateutil import parser
from ftx import FtxClient

with open("configuration.yml", "r") as f:
    config = yaml.safe_load(f)

ftx = FtxClient(api_key=config["ftx"]["api_key"],
                api_secret=config["ftx"]["api_secret"],
                subaccount_name=config["ftx"]["account"])


def _reconnect_ftx():
    global ftx
    ftx = FtxClient(api_key=config["ftx"]["api_key"],
                    api_secret=config["ftx"]["api_secret"],
                    subaccount_name=config["ftx"]["account"])


def get_ftx_fills(start_time: float, end_time: float) -> pd.DataFrame:
    _reconnect_ftx()
    fills = list(reversed(ftx.get_fills(start_time=start_time, end_time=end_time)))
    df = pd.DataFrame(columns=fills[0].keys())

    for idx, fill in enumerate(fills):
        df.loc[idx] = fill.values()

    df = df.drop(["id", "baseCurrency", "quoteCurrency", "feeCurrency", "market",
                  "future", "type", "liquidity", "tradeId", "feeRate"], axis=1)
    df["time"] = [parser.parse(x) for x in df["time"]]
    df = df.groupby("orderId").agg({"side": min, 'price': min, 'size': sum,
                                    'time': min, "fee": sum}).set_index("time")
    return df


def get_historical_data(start_time: float, end_time: float, resolution: int = 300) -> pd.DataFrame:
    _reconnect_ftx()

    data = ftx.get_historical_data("BTC-PERP", resolution=resolution, limit=10000,
                                   start_time=start_time, end_time=end_time)
    df = pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])

    for idx, item in enumerate(data):
        df.loc[idx] = [parser.parse(item["startTime"]), item["open"], item["high"],
                       item["low"], item["close"], item["volume"]]

    df = df.set_index("time")
    return df
