from datetime import datetime
from decimal import Decimal

import plotly.graph_objects as go


def plot_candles(
    *,
    x: list[datetime],
    open: list[Decimal],
    high: list[Decimal],
    low: list[Decimal],
    close: list[Decimal],
    symbol: str,
):
    candlestick = go.Candlestick(
        x=x,
        open=open,
        high=high,
        low=low,
        close=close,
        # volume=[candle.volume for candle in candles],
    )

    layout = go.Layout(
        title=f"Candlestick Chart for {symbol}",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Price"),
    )

    return go.Figure(data=[candlestick], layout=layout)
