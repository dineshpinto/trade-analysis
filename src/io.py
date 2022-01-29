import ast
import os
import pickle
import re
from typing import Tuple

import pandas as pd
from dateutil import parser


def add_into_dataframe(df: pd.DataFrame, filepath: str) -> pd.DataFrame:
    if os.path.exists(filepath):
        df1 = pd.read_csv(filepath, index_col="time", parse_dates=["time"],
                          infer_datetime_format=True)
    else:
        df.to_csv(filepath)
        return df

    df = pd.concat([df, df1])
    df = df[~df.index.duplicated(keep='first')]
    df = df.sort_index()
    df.to_csv(filepath)
    return df


def _insert_unique_ids(list1: list, list2: list) -> list:
    list_ids = [element["id"] for element in list1]

    for element in list2:
        if element["id"] not in list_ids:
            list1.append(element)

    return list1


def _read_from_pickle(filepath: str) -> list:
    if os.path.exists(filepath):
        with open(filepath, 'rb') as file:
            list1 = pickle.load(file)
        return list1
    else:
        return []


def _write_to_pickle(filepath: str, list1: list):
    with open(filepath, 'wb') as file:
        pickle.dump(list1, file)


def add_into_pickle(list1: list, filepath: str) -> list:
    list1 = _insert_unique_ids(_read_from_pickle(filepath), list1)
    _write_to_pickle(filepath, list1)
    return list1


def parse_logfile(filepath: str) -> Tuple[pd.DataFrame, list, list, list]:
    df = pd.DataFrame(columns=["time", "price", "funding_rate"])

    orders = []
    stop_losses = []
    take_profits = []

    idx = 0
    with open(filepath, 'r') as file:
        for line in file:
            if not any(s in line for s in ["HOLDING", "ORDER", "STOP_LOSS",
                                           "TAKE_PROFIT", "POSITION"]):
                if "BTC-PERP" in line:
                    try:
                        match = re.findall("-?\d*\.?\d+", line)
                        time = parser.parse(line[:29])
                        price = float(match[9])
                        funding_rate = float(match[12]) * 10 ** int(match[13])
                        df.loc[idx] = [time, price, funding_rate]
                        idx += 1
                    except Exception as exc:
                        print(line)
                        print(match)
                        raise exc
            if "ORDER" in line:
                orders.append(ast.literal_eval(line[55:]))
            if "STOP_LOSS" in line:
                stop_losses.append(ast.literal_eval(line[59:]))
            if "TAKE_PROFIT" in line:
                take_profits.append(ast.literal_eval(line[61:]))
            if "Exception" in line:
                print(line)
                raise Exception

    df = df.set_index("time")
    return df, orders, stop_losses, take_profits
