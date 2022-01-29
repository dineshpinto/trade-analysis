from typing import Tuple

import matplotlib.pyplot as plt
import pandas as pd


def get_orders(target_funding_rate_change: float, df: pd.DataFrame, ax: plt.subplot, plot: bool) \
        -> Tuple[list, list]:
    order_indexes = []
    positions = []

    for idx in range(len(df.funding_rate) - 1):
        current_rate_shifted = df.funding_rate[idx] + 1
        next_rate_shifted = df.funding_rate[idx + 1] + 1

        funding_rate_change = abs(current_rate_shifted - next_rate_shifted) / next_rate_shifted * 100

        if funding_rate_change > target_funding_rate_change:
            if current_rate_shifted > next_rate_shifted:
                positions.append("sell")
                if plot:
                    ax.axvline(df.index[idx + 1], color="tab:red", linestyle="--")
            else:
                positions.append("buy")
                if plot:
                    ax.axvline(df.index[idx + 1], color="tab:green", linestyle="--")

            # ax2.axhline(df.price[idx + 1], color="tab:grey", linestyle="--")
            # ax2.axhline(df.price[idx + 1] + 0.01 * df.price[idx + 1], color="tab:green", linestyle="--")
            # ax2.axhline(df.price[idx + 1] - 0.01 * df.price[idx + 1], color="tab:red", linestyle="--")

            order_indexes.append(idx + 1)

    return order_indexes, positions


def get_tp_and_sl(tp_percent: float, sl_percent: float, order_indexes: list, positions: list,
                  df: pd.DataFrame, ax: plt.subplot, plot: bool) -> Tuple[list, list]:
    take_profits, stop_losses = [], []

    for idx in range(len(order_indexes)):
        price = df.price[order_indexes[idx]]

        if idx < len(order_indexes) - 1:
            end_idx = order_indexes[idx + 1]
        else:
            end_idx = -1

        if positions[idx] == "buy":
            take_profit = price + tp_percent / 100 * price
            stop_loss = price - sl_percent / 100 * price
        elif positions[idx] == "sell":
            take_profit = price - tp_percent / 100 * price
            stop_loss = price + sl_percent / 100 * price
        else:
            raise ValueError(f"Invalid position {positions[idx]}")

        if plot:
            ax.plot((df.index[order_indexes[idx]], df.index[end_idx]),
                    (take_profit, take_profit),
                    linestyle="--", color='tab:green', alpha=0.5)
            ax.plot((df.index[order_indexes[idx]], df.index[end_idx]),
                    (stop_loss, stop_loss),
                    linestyle="--", color='tab:red', alpha=0.5)

        take_profits.append(take_profit)
        stop_losses.append(stop_loss)

    return take_profits, stop_losses


def get_profitability(order_indexes: list, positions: list, take_profits: list, stop_losses: list,
                      df: pd.DataFrame, df_price: pd.DataFrame, ax: plt.subplot, plot: bool) -> list:
    profitability = []

    for idx in range(len(order_indexes)):
        profit_pct = None

        idx1 = df_price.index.get_loc(df.index[order_indexes[idx]], method='nearest')
        if idx == len(order_indexes) - 1:
            idx2 = len(df_price.index) - 1
        else:
            idx2 = df_price.index.get_loc(df.index[order_indexes[idx + 1]], method='nearest')

        if positions[idx] == "buy":
            max_idx = [i for i, val in enumerate(df_price.high[idx1:idx2]) if val >= take_profits[idx]]
            min_idx = [i for i, val in enumerate(df_price.low[idx1:idx2]) if val <= stop_losses[idx]]

            if max_idx:
                profit_pct = (take_profits[idx] - df_price.close[idx1]) / df_price.close[idx1] * 100
            if min_idx:
                profit_pct = (stop_losses[idx] - df_price.close[idx1]) / df_price.close[idx1] * 100
            if min_idx and max_idx:
                if min_idx[0] < max_idx[0]:
                    profit_pct = (stop_losses[idx] - df_price.close[idx1]) / df_price.close[idx1] * 100
                else:
                    profit_pct = (take_profits[idx] - df_price.close[idx1]) / df_price.close[idx1] * 100
            if not min_idx and not max_idx:
                profit_pct = (df_price.close[idx2] - df_price.close[idx1]) / df_price.close[idx1] * 100
        elif positions[idx] == "sell":
            min_idx = [i for i, val in enumerate(df_price.low[idx1:idx2]) if val <= take_profits[idx]]
            max_idx = [i for i, val in enumerate(df_price.high[idx1:idx2]) if val >= stop_losses[idx]]

            if min_idx:
                profit_pct = (df_price.close[idx1] - take_profits[idx]) / take_profits[idx] * 100
            if max_idx:
                profit_pct = (df_price.close[idx1] - stop_losses[idx]) / stop_losses[idx] * 100
            if min_idx and max_idx:
                if max_idx[0] < min_idx[0]:
                    profit_pct = (df_price.close[idx1] - stop_losses[idx]) / stop_losses[idx] * 100
                else:
                    profit_pct = (df_price.close[idx1] - take_profits[idx]) / take_profits[idx] * 100
            if not min_idx and not max_idx:
                profit_pct = (df_price.close[idx1] - df_price.close[idx2]) / df_price.close[idx2] * 100

        profitability.append(profit_pct)

        if plot:
            if profit_pct > 0:
                color = "tab:green"
            else:
                color = "tab:red"

            center_point = (idx1 + idx2) // 2
            ax.text(df_price.index[center_point], df_price.high.max(), f"{profit_pct:.1f}%",
                    horizontalalignment='center', verticalalignment='center', rotation=90, color=color)
            ax.axvspan(df_price.index[idx1 + 5], df_price.index[idx2 - 5], color=color, alpha=0.3)

    return profitability


def test_trade_setup(target_funding_rate_change, tp_percent, sl_percent, df, df_price, ax1, ax2, plot=True) \
        -> Tuple[list, list, list, list, list]:
    order_indexes, positions = get_orders(target_funding_rate_change, df=df, ax=ax1, plot=plot)
    take_profits, stop_losses = get_tp_and_sl(tp_percent, sl_percent, order_indexes, positions, df, ax=ax2,
                                              plot=plot)
    profitability = get_profitability(order_indexes, positions, take_profits, stop_losses, df, df_price, ax=ax2,
                                      plot=plot)
    return order_indexes, positions, take_profits, stop_losses, profitability
