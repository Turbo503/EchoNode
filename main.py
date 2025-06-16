"""EchoNode command line entry point."""

import argparse

from echonode.gui import run_gui

# Placeholder hooks for future ML modules

def run_live():
    """Run live trading with ML hooks (placeholder)."""
    print("Live trading mode not yet implemented. GUI will open instead.")
    run_gui()


def retrain_models():
    """Retrain ML models (placeholder)."""
    print("Retraining models... (placeholder)")


def parse_args():
    parser = argparse.ArgumentParser(description="EchoNode trading application")
    parser.add_argument("mode", nargs="?", default="gui", choices=["gui", "live", "retrain"],
                        help="Mode to run")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.mode == "gui":
        run_gui()
    elif args.mode == "live":
        run_live()
    elif args.mode == "retrain":
        retrain_models()


if __name__ == "__main__":
    main()
