"""Tkinter-based GUI components for EchoNode."""

from __future__ import annotations

import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import mplfinance as mpf

from .trading import get_exchange, place_order
from .indicators import compute_divergence

DATA_DIR = Path(__file__).resolve().parent / "data" / "ohlcv_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class IndicatorPopup(tk.Toplevel):
    """Popup window for toggling indicators."""

    def __init__(self, parent: tk.Widget, indicators: list[str], callback):
        super().__init__(parent)
        self.callback = callback
        self.vars: dict[str, tk.BooleanVar] = {}
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)
        for name in indicators:
            var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(
                frame,
                text=name,
                variable=var,
                command=lambda n=name, v=var: self.callback(n, v.get()),
            )
            chk.pack(anchor="w")
            self.vars[name] = var
        self.bind("<FocusOut>", lambda e: self.withdraw())

    def show_at(self, x: int, y: int):
        self.geometry(f"+{x}+{y}")
        self.deiconify()
        self.focus_set()


class CandlestickCanvas:
    """Matplotlib canvas for candlestick data."""

    def __init__(self, master: tk.Widget):
        self.fig = Figure(tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.widget = self.canvas.get_tk_widget()
        self.widget.pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)

        self._data = pd.DataFrame()
        self.indicator_data: dict[str, pd.DataFrame] = {}
        self.indicators_enabled: dict[str, bool] = {"Divergence": False}
        self._crosshair_v = self.ax.axvline(color="gray", lw=0.5, ls="--")
        self._crosshair_h = self.ax.axhline(color="gray", lw=0.5, ls="--")

    def set_indicator_state(self, name: str, state: bool):
        self.indicators_enabled[name] = state
        self.redraw()

    def load_data(self, df: pd.DataFrame):
        self._data = df
        self.indicator_data["Divergence"] = compute_divergence(df)
        self.redraw()

    def redraw(self):
        self.ax.clear()
        if not self._data.empty:
            print("Redrawing chart with", len(self._data), "rows")
            mpf.plot(
                self._data,
                type="candle",
                ax=self.ax,
                datetime_format="%H:%M",
            )
            if self.indicators_enabled.get("Divergence"):
                div = self.indicator_data.get("Divergence")
                if div is not None:
                    bulls = div["Bullish"].dropna()
                    bears = div["Bearish"].dropna()
                    if not bulls.empty:
                        self.ax.scatter(
                            bulls.index,
                            bulls.values,
                            marker="^",
                            color="green",
                            zorder=5,
                        )
                    if not bears.empty:
                        self.ax.scatter(
                            bears.index,
                            bears.values,
                            marker="v",
                            color="red",
                            zorder=5,
                        )
        self._crosshair_v = self.ax.axvline(color="gray", lw=0.5, ls="--")
        self._crosshair_h = self.ax.axhline(color="gray", lw=0.5, ls="--")
        self.canvas.draw_idle()

    def on_mouse_move(self, event):
        if event.inaxes != self.ax:
            return
        if event.xdata is None or event.ydata is None:
            return
        self._crosshair_v.set_xdata([event.xdata, event.xdata])
        self._crosshair_h.set_ydata([event.ydata, event.ydata])
        self.canvas.draw_idle()


class MainWindow(tk.Tk):
    """Main application window."""

    def __init__(self, symbol: str = "BTC/USDT", timeframe: str = "1m"):
        super().__init__()
        self.symbol = symbol
        self.timeframe = timeframe
        self.title("EchoNode")
        self.geometry("900x600")

        self.exchange = None
        self.update_thread: threading.Thread | None = None

        self.canvas = CandlestickCanvas(self)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x")
        self.buy_button = ttk.Button(btn_frame, text="Buy", command=lambda: self.place_order("buy"))
        self.sell_button = ttk.Button(btn_frame, text="Sell", command=lambda: self.place_order("sell"))
        self.indicator_button = ttk.Button(btn_frame, text="Indicators", command=self.show_indicator_popup)
        self.buy_button.pack(side="left")
        self.sell_button.pack(side="left")
        self.indicator_button.pack(side="left")

        self.indicator_popup = IndicatorPopup(self, ["Divergence"], self.canvas.set_indicator_state)

        self.update_interval_ms = 60_000
        self.after(0, self.update_chart)

    def show_indicator_popup(self):
        x = self.indicator_button.winfo_rootx()
        y = self.indicator_button.winfo_rooty() + self.indicator_button.winfo_height()
        self.indicator_popup.show_at(x, y)

    def _get_exchange(self):
        if self.exchange is None:
            self.exchange = get_exchange()
        return self.exchange

    def fetch_data(self) -> pd.DataFrame:
        print("Fetching OHLCV for", self.symbol)
        ex = self._get_exchange()
        ohlcv = ex.fetch_ohlcv(self.symbol, timeframe=self.timeframe, limit=200)
        df = pd.DataFrame(
            ohlcv,
            columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"],
        )
        df["Date"] = pd.to_datetime(df["Timestamp"], unit="ms")
        df.set_index("Date", inplace=True)
        df = df[["Open", "High", "Low", "Close", "Volume"]]
        print("Fetched", len(df), "rows")
        return df

    def update_chart(self):
        if self.update_thread and self.update_thread.is_alive():
            print("Update already in progress")
            self.after(self.update_interval_ms, self.update_chart)
            return

        def task():
            try:
                print("Starting chart update")
                df = self.fetch_data()
                path = DATA_DIR / f"{self.symbol.replace('/', '')}.csv"
                df.to_csv(path)
                print("Saved CSV to", path)
                self.after(0, lambda: self.canvas.load_data(df))
                print("Queued data for drawing")
            except Exception as exc:
                print("Error updating chart:", exc)
            finally:
                self.update_thread = None

        self.update_thread = threading.Thread(target=task, daemon=True)
        self.update_thread.start()
        self.after(self.update_interval_ms, self.update_chart)

    def place_order(self, side: str):
        ex = self._get_exchange()
        try:
            place_order(ex, self.symbol, side, amount=0.001)
        except Exception as exc:
            messagebox.showerror("Order Error", str(exc))


def run_gui():
    app = MainWindow()
    app.mainloop()
