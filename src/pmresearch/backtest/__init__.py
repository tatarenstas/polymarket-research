"""Point-in-time backtesting on the on-chain trade tape.

Execution model (no historical order book exists, so fills are proxied by real fills):

* A signal at time ``t`` wants to buy side ``s`` (+1 = the reference/"Yes" token,
  -1 = the opposite token).
* The entry is the first real taker trade in the same market and the same economic
  direction (``d = s``) at or after ``t + latency``. That taker paid the ask on our
  side, so its price is a fill we could also have obtained (ignoring queue/size).
  No entry within ``window`` seconds means no trade.
* Cost per share: ``p`` for s=+1, ``1-p`` for s=-1. Payoff at resolution: ``y`` or
  ``1-y``. The entry trade's own fee rate is charged.
* Exits before resolution use the first opposite-direction taker trade (we sell into
  the bid) at or after the exit time.
"""
