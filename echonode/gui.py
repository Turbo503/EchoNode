"""GUI components for EchoNode."""

import sys
import threading
from pathlib import Path

import pandas as pd
import ccxt
from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import mplfinance as mpf

from .trading import get_exchange, place_order

DATA_DIR = Path(__file__).resolve().parent / "data" / "ohlcv_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class CandlestickCanvas(FigureCanvas):
    """Matplotlib canvas showing candlestick data."""

    def __init__(self, parent=None):
        self.fig = Figure(tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)
        self._data = pd.DataFrame()
        self.mpl_connect("motion_notify_event", self.on_mouse_move)
        self._crosshair_v = self.ax.axvline(color="gray", lw=0.5, ls="--")
        self._crosshair_h = self.ax.axhline(color="gray", lw=0.5, ls="--")

    def load_data(self, df: pd.DataFrame):
        self._data = df
        self.redraw()

    def redraw(self):
        self.ax.clear()
        if not self._data.empty:
            mpf.plot(self._data, type="candle", ax=self.ax, datetime_format="%H:%M")
        self.draw()

    def on_mouse_move(self, event):
        if event.inaxes != self.ax:
            return
        self._crosshair_v.set_xdata(event.xdata)
        self._crosshair_h.set_ydata(event.ydata)
        self.draw_idle()


class MainWindow(QtWidgets.QWidget):
    """Main application window."""

    def __init__(self, symbol: str = "BTC/USDT", timeframe: str = "1m"):
        super().__init__()
        self.symbol = symbol
        self.timeframe = timeframe
        self.setWindowTitle("EchoNode")
        self.resize(900, 600)

        self.exchange = None
        self.canvas = CandlestickCanvas(self)
        self.buy_button = QtWidgets.QPushButton("Buy")
        self.sell_button = QtWidgets.QPushButton("Sell")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.canvas)
        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(self.buy_button)
        buttons.addWidget(self.sell_button)
        layout.addLayout(buttons)

        self.buy_button.clicked.connect(lambda: self.place_order("buy"))
        self.sell_button.clicked.connect(lambda: self.place_order("sell"))

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_chart)
        self.timer.start(60_000)  # update every minute

        self.update_chart()

    def _get_exchange(self):
        if self.exchange is None:
            self.exchange = get_exchange()
        return self.exchange

    def fetch_data(self) -> pd.DataFrame:
        ex = self._get_exchange()
        ohlcv = ex.fetch_ohlcv(self.symbol, timeframe=self.timeframe, limit=200)
        df = pd.DataFrame(ohlcv, columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"])
        df["Date"] = pd.to_datetime(df["Timestamp"], unit="ms")
        df.set_index("Date", inplace=True)
        df = df[["Open", "High", "Low", "Close", "Volume"]]
        return df

    def update_chart(self):
        def task():
            df = self.fetch_data()
            path = DATA_DIR / f"{self.symbol.replace('/', '')}.csv"
            df.to_csv(path)
            QtCore.QMetaObject.invokeMethod(self.canvas, lambda: self.canvas.load_data(df), QtCore.Qt.QueuedConnection)
        threading.Thread(target=task, daemon=True).start()

    def place_order(self, side: str):
        ex = self._get_exchange()
        try:
            place_order(ex, self.symbol, side, amount=0.001)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Order Error", str(exc))


def run_gui():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
