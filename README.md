# EchoNode

EchoNode is a cross‑platform desktop trading application inspired by TradingView. It fetches market data from the Bitunix exchange and displays real‑time candlestick charts. You can place live orders directly from the interface using the Bitunix REST API via **ccxt**.

## Features
* Real‑time candlestick chart with pan, zoom and crosshair.
* Buy/Sell buttons for immediate market orders.
* API credentials loaded from `BITUNIX_KEY` and `BITUNIX_SECRET` environment variables.
* Works on Windows, macOS and Linux using **PyQt5**.
* Hooks for future machine learning models (TCN/TFT/PPO) to generate trading signals.

## Requirements
Install the dependencies:
```bash
pip install -r requirements.txt
```
Set your API keys as environment variables:
```bash
export BITUNIX_KEY=your_key
export BITUNIX_SECRET=your_secret
```

## Usage
Running without arguments launches the GUI:
```bash
python main.py
```
Available commands:
```bash
python main.py gui       # launch the charting GUI
python main.py live      # run live trading mode (uses ML hooks)
python main.py retrain   # force a model retrain (placeholder)
```
Price history downloaded from Bitunix is stored in `data/ohlcv_data` as CSV files.

## License
The code is released under the Business Source License 1.1 and becomes Apache-2.0 on 2029-01-01.
