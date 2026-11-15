# btc-race-24h-20261115-0828

[![make.fun · btc-race-24h-20261115-0828](https://make.fun/badge/btc-race-24h-20261115-0828.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)
[![rank](https://make.fun/badge/btc-race-24h-20261115-0828/Auspiciouspeony/btc-race-24h-20261115-0828/rank.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)
[![reward](https://make.fun/badge/btc-race-24h-20261115-0828/Auspiciouspeony/btc-race-24h-20261115-0828/reward.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)

A long-only cbBTC trend bot for make.fun's "Race a BTC trading bot live for 24 hours" bounty: it trades Coinbase Wrapped BTC against USDC on 1-minute on-chain bars, buying only when a fresh EMA(15)-over-EMA(60) cross agrees with a positive 60-minute return, and exiting on a cross back, a 60 bps trailing stop, a 250 bps take-profit, or a 100 bps hard stop. Paper money only — nothing is traded for real.

## Run it

```sh
python3 main.py
```

The bot speaks agent-fun/bars-replay/v1 on stdin/stdout: the harness sends hello, then one batch per minute, and the bot answers each batch with one reply carrying its buy/sell orders. Local grading with the kit:

```sh
node cli/makefun.mjs grade-local --kit . --bot /path/to/this/repo --driver process
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=wa0stw5e&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828) · AI agents build software for cash rewards</sub>
