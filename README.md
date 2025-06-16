# EchoNode


Run `python main.py` to launch the GUI. The interface lets you start live
trading, retrain the models or view stored charts. You can also call the modes
directly:
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
Running `python main.py` without any arguments launches the GUI directly:
```bash
python main.py
```

Alternatively you can call the modes directly:
```bash
python main.py live      # run live trading
python main.py retrain   # force a model retrain
python main.py gui       # launch the charting GUI

```
When you choose "View Charts" the GUI downloads the latest data from Bitunix
for the selected pair and displays a price chart. Downloaded CSV files are saved
under `data/ohlcv_data`.


The live mode checks the clock every minute and when the minute equals `0` it
fetches the last 64 hours of data, generates features and decides whether to go
short, flat or long with a 0.001 BTC order. Retrain mode runs the weekly
training routine.


## License
The code is released under the Business Source License 1.1. It becomes Apache-2.0 on 2029-01-01.
