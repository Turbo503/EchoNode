"""GUI components for EchoNode."""

import sys
import threading
from pathlib import Path

import pandas as pd
from PyQt5 import QtWidgets, QtCore, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import mplfinance as mpf

from .trading import get_exchange, place_order
from .indicators import compute_divergence


class IndicatorPopup(QtWidgets.QListWidget):
    """Popup list for toggling indicators."""

    toggled = QtCore.pyqtSignal(str, bool)

    def __init__(self, indicators: list[str]):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.Popup)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        for name in indicators:
            item = QtWidgets.QListWidgetItem(name)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.addItem(item)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        item = self.itemAt(event.pos())
        if item is not None:
            checked = item.checkState() == QtCore.Qt.Checked
            item.setCheckState(QtCore.Qt.Unchecked if checked else QtCore.Qt.Checked)
            self.toggled.emit(item.text(), not checked)
            event.accept()
            return
        super().mousePressEvent(event)

    def focusOutEvent(self, event: QtGui.QFocusEvent):
        self.hide()
        super().focusOutEvent(event)

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
        self.indicator_data: dict[str, pd.DataFrame] = {}
        self.indicators_enabled: dict[str, bool] = {"Divergence": False}
        self.mpl_connect("motion_notify_event", self.on_mouse_move)
        self._crosshair_v = self.ax.axvline(color="gray", lw=0.5, ls="--")
        self._crosshair_h = self.ax.axhline(color="gray", lw=0.5, ls="--")

    def set_indicator_state(self, name: str, state: bool):
        self.indicators_enabled[name] = state
        self.redraw()

    def load_data(self, df: pd.DataFrame):
        self._data = df
        # pre-compute indicator data
        self.indicator_data["Divergence"] = compute_divergence(df)
        self.redraw()

    def redraw(self):
        self.ax.clear()
        if not self._data.empty:
            mpf.plot(self._data, type="candle", ax=self.ax, datetime_format="%H:%M")
            if self.indicators_enabled.get("Divergence"):
                div = self.indicator_data.get("Divergence")
                if div is not None:
                    bulls = div["Bullish"].dropna()
                    bears = div["Bearish"].dropna()
                    if not bulls.empty:
                        self.ax.scatter(bulls.index, bulls.values, marker="^", color="green", zorder=5)
                    if not bears.empty:
                        self.ax.scatter(bears.index, bears.values, marker="v", color="red", zorder=5)
        self.draw()

    def on_mouse_move(self, event):
        if event.inaxes != self.ax:
            return
        if event.xdata is None or event.ydata is None:
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
        self.indicator_button = QtWidgets.QPushButton("Indicators")
        self.indicator_popup = IndicatorPopup(["Divergence"])
        self.indicator_popup.toggled.connect(self.canvas.set_indicator_state)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.canvas)
        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(self.buy_button)
        buttons.addWidget(self.sell_button)
        buttons.addWidget(self.indicator_button)
        layout.addLayout(buttons)

        self.indicator_button.clicked.connect(self.show_indicator_popup)

        self.buy_button.clicked.connect(lambda: self.place_order("buy"))
        self.sell_button.clicked.connect(lambda: self.place_order("sell"))

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_chart)
        self.timer.start(60_000)  # update every minute

        self.update_chart()

    def show_indicator_popup(self):
        pos = self.indicator_button.mapToGlobal(QtCore.QPoint(0, self.indicator_button.height()))
        self.indicator_popup.move(pos)
        self.indicator_popup.show()

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
