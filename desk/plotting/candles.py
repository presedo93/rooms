from datetime import datetime
from decimal import Decimal

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_candles(
    *,
    x: list[datetime],
    open: list[Decimal],
    high: list[Decimal],
    low: list[Decimal],
    close: list[Decimal],
    volume: list[Decimal],
):
    color = ["green" if c > o else "red" for c, o in zip(close, open)]

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0
    )

    candlestick = go.Candlestick(x=x, open=open, high=high, low=low, close=close, showlegend=False)
    volumes = go.Bar(x=x, y=volume, marker_color=color, name="Volume", showlegend=False)

    fig.add_trace(candlestick, 1, 1)
    fig.add_trace(volumes, 2, 1)

    fig.update_xaxes(rangeslider_visible=False)

    return fig
