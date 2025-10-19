from datetime import datetime
from decimal import Decimal

import plotly.graph_objects as go
from plotly.subplots import make_subplots

INC_COLOR = "#3D9970"
DEC_COLOR = "#FF4136"


VOL_PARAMS = {"name": "Volume", "showlegend": False}
OHLC_PARAMS = {"showlegend": False}


def plot_candles(
    *,
    x: list[datetime],
    open: list[Decimal],
    high: list[Decimal],
    low: list[Decimal],
    close: list[Decimal],
    volume: list[Decimal],
):
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0
    )

    color = [INC_COLOR if c > o else DEC_COLOR for c, o in zip(close, open)]
    ohlc = go.Ohlc(x=x, open=open, high=high, low=low, close=close, **OHLC_PARAMS)
    volumes = go.Bar(x=x, y=volume, marker_color=color, **VOL_PARAMS)

    fig.add_trace(ohlc, 1, 1)
    fig.add_trace(volumes, 2, 1)
    fig.update_xaxes(rangeslider_visible=False)

    return fig
