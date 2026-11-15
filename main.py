"""Bounce-catcher: a long-only cbBTC trend bot for agent-fun/bars-replay/v1.

Idea: on 1-minute bars Bitcoin mostly chops sideways, so plain EMA crosses
whipsaw and bleed the ~26 bps round-trip cost. This bot only buys when three
things agree on the same bar close -- a fresh fast-over-slow EMA cross, the
price already up over the last hour, and a slow trend that is not falling --
and then it exits on the first of a cross back down, a trailing stop, a
take-profit, or a hard stop. It sits in cash the rest of the time: on the
dev window it traded twice and stayed flat for the first twelve hours.

Protocol: the harness sends hello once, then one batch per minute (the bar
that just closed, the fills of the previous batch's orders, the account),
then done. Every batch gets exactly one reply echoing its seq. Orders
decided on a batch fill at the next bar's open, so every decision uses only
closes the bot has already been sent. No clock, no network, no randomness:
the same bars always give the same orders.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

# --- strategy knobs (all in bars or basis points) ---------------------------
FAST_SPAN = 15          # fast EMA span, in 1-minute closes
SLOW_SPAN = 60          # slow EMA span
RET60_MIN_BPS = 40      # entry needs the close up >= 40 bps over the last hour
TRAIL_BPS = 60          # trailing stop: sell once the close falls 60 bps off the high
TAKE_BPS = 250          # take-profit: sell once the position is up 250 bps on cost
STOP_BPS = 100          # hard stop: sell once the position is down 100 bps on cost
MAX_SLIPPAGE_BPS = 100  # 1% past the close the order was decided on
MIN_NOTIONAL = 1_000_000  # 1 USDC, in quote units


class Ema:
    """One exponential moving average over integer closes.

    Seeds as the plain mean of its first span of closes, then moves
    2 / (span + 1) of the way to each new close. Float64, so the same
    closes always give the same value.
    """

    def __init__(self, span):
        self.span = span
        self.alpha = 2.0 / (span + 1)
        self.warm = []
        self.value = None

    def push(self, close):
        if self.value is not None:
            self.value += self.alpha * (close - self.value)
            return
        self.warm.append(close)
        if len(self.warm) == self.span:
            self.value = sum(self.warm) / self.span


class Bot:
    """The strategy state: two EMAs, the close history, and the open trade."""

    def __init__(self):
        self.fast = Ema(FAST_SPAN)
        self.slow = Ema(SLOW_SPAN)
        self.closes = []
        self.prev_gap = None
        self.entry_high = None

    def ret_bps(self, bars_back):
        """Return of the latest close against the close `bars_back` bars ago, in bps."""
        if len(self.closes) <= bars_back:
            return None
        then = self.closes[-1 - bars_back]
        return (self.closes[-1] - then) * 10_000 // then

    def on_batch(self, state, batch):
        # A minute with no bar for our symbol adds nothing: never reuse a stale close.
        if not any(b["symbol"] == SYMBOL for b in batch["bars"]):
            return []
        close = state.close(SYMBOL)
        if close is None:
            return []
        self.closes.append(close)
        self.fast.push(close)
        self.slow.push(close)
        if self.fast.value is None or self.slow.value is None:
            return []
        gap = self.fast.value - self.slow.value
        prev_gap = self.prev_gap
        self.prev_gap = gap

        held = state.positions.get(SYMBOL)
        if held is not None:
            if self.entry_high is None or close > self.entry_high:
                self.entry_high = close
            value = state.value(SYMBOL, held.qty)
            pnl_bps = (value - held.cost) * 10_000 // held.cost if held.cost else 0
            trail_bps = (self.entry_high - close) * 10_000 // self.entry_high
            cross_down = prev_gap is not None and gap < 0 and prev_gap >= 0
            if cross_down or trail_bps >= TRAIL_BPS or pnl_bps >= TAKE_BPS or pnl_bps <= -STOP_BPS:
                self.entry_high = None
                return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
            return []

        # Flat: wait for a fresh cross up with the hour's return behind it.
        if state.warming_up:
            return []
        cross_up = prev_gap is not None and gap > 0 and prev_gap <= 0
        ret60 = self.ret_bps(60)
        if cross_up and ret60 is not None and ret60 >= RET60_MIN_BPS:
            if state.cash < MIN_NOTIONAL:
                return []
            self.entry_high = close
            return [{"side": "buy", "symbol": SYMBOL, "notional_quote_units": state.cash,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []


makefun_bars.run(Bot().on_batch)
