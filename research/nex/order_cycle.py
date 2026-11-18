"""NEX sandbox (Polygon Amoy) smoke test: one post-only order through its full lifecycle, timed.

Runs ONLY on the allowlisted server (89.167.103.214). Secrets are read from environment
variables (load them from /root/.nex.env, chmod 600); nothing secret is printed or logged.

  POLYMARKET_PRIVATE_KEY   test EOA key (sandbox only, never a mainnet key)
  GAMMA_CLIENT_ID          Gamma/relayer edge credentials from onboarding
  GAMMA_CLIENT_SECRET
  BUILDER_CODE             optional builder code (bytes32 hex), attached to orders
  AMOY_RPC_URL             optional, default https://polygon-amoy-bor-rpc.publicnode.com

Steps: /health -> Gamma market list -> client -> approvals + pUSD balance -> order book ->
post-only BUY at one tick, minimum size (rests far from the market) -> read back -> cancel.
With --check it stops before placing anything. Approvals are only sent with
--setup-approvals (they cost test POL).

Usage on the server:
  set -a; . /root/.nex.env; set +a
  /root/nex/.venv/bin/python /root/nex/order_cycle.py --check
  /root/nex/.venv/bin/python /root/nex/order_cycle.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import socket
import time
from dataclasses import replace

# The edge (Gamma, relayer) allowlists only our IPv4 /32, but the server prefers IPv6 and
# CloudFront answers on both, so IPv6 requests get 403 "invalid edge credentials".
# Force IPv4 for every lookup in this process (covers httpx and the SDK's own clients).
_getaddrinfo = socket.getaddrinfo


def _ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
    return _getaddrinfo(host, port, socket.AF_INET, type, proto, flags)


socket.getaddrinfo = _ipv4_only

import httpx
from eth_account import Account
from polymarket import AsyncSecureClient, Market
from polymarket._internal.environment import PRODUCTION_CONFIG, create_environment

NEX = "https://nex.preprod.defi.euw2.polymarket.sh"
NEX_WS = "wss://nex-ws.preprod.defi.euw2.polymarket.sh"
GAMMA = "https://gamma-api-preprod.polymarket.dev"
RELAYER = "https://relayer-preprod.polymarket.dev"
EXCHANGE_V3 = "0xe3333700cA9d93003F00f0F71f8515005F6c00Aa"  # Amoy, from the NEX trading guide
POSITION_MANAGER = "0x006F54F7f9A22e0000CC2AB60031000000ae9fEF"


def need(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"missing env var {name} (load /root/.nex.env first)")
    return v


class Timer:
    def __init__(self) -> None:
        self.rows: list[tuple[str, float]] = []

    async def run(self, label: str, coro):
        t = time.perf_counter()
        out = await coro
        ms = (time.perf_counter() - t) * 1000
        self.rows.append((label, ms))
        print(f"  {label:<28} {ms:8.1f} ms")
        return out


async def main(args) -> None:
    pk = need("POLYMARKET_PRIVATE_KEY")
    gid, gsec = need("GAMMA_CLIENT_ID"), need("GAMMA_CLIENT_SECRET")
    eoa = Account.from_key(pk).address
    print(f"EOA {eoa}")
    tm = Timer()

    async with httpx.AsyncClient(timeout=15) as h:
        r = await tm.run("GET /health", h.get(f"{NEX}/health"))
        print(f"  health HTTP {r.status_code}")
        r = await tm.run("Gamma /markets/keyset", h.get(
            f"{GAMMA}/markets/keyset", headers={"x-client-id": gid, "x-client-secret": gsec},
            params=[("closed", "false"), ("version", "v2"), ("limit", "20")]))
        r.raise_for_status()
    markets = []
    for item in r.json()["markets"]:
        if isinstance(item.get("outcomes"), str):
            item["outcomes"] = json.loads(item["outcomes"])
        if len(item.get("outcomes") or []) == 2:
            markets.append(Market.parse_response(item))
    open_ = [m for m in markets if m.state.accepting_orders and m.outcomes.yes.position_id]
    print(f"  markets: {len(markets)} binary, {len(open_)} accepting orders")
    if not open_:
        raise SystemExit("no market accepting orders")
    market = open_[0]
    asset = market.outcomes.yes.position_id
    print(f"  market: {market.question[:70]}")

    env = create_environment(name="amoy", config=replace(
        PRODUCTION_CONFIG, chain_id=80002,
        rpc_url=os.environ.get("AMOY_RPC_URL", "https://polygon-amoy-bor-rpc.publicnode.com"),
        clob_url=NEX, clob_market_ws_url=f"{NEX_WS}/ws/market", clob_user_ws_url=f"{NEX_WS}/ws/user",
        gamma_url=GAMMA, relayer_url=RELAYER, exchange_v3=EXCHANGE_V3, position_manager=POSITION_MANAGER))
    client = await tm.run("client create (auth)", AsyncSecureClient.create(private_key=pk, wallet=eoa, environment=env))
    try:
        appr = await tm.run("approvals state", client.get_trading_approvals_state())
        print(f"  approvals: {appr}")
        bal = await tm.run("pUSD balance/allowance", client.get_balance_allowance(asset_type="COLLATERAL"))
        print(f"  collateral: {bal}")
        if args.setup_approvals:
            handle = await tm.run("setup approvals (tx)", client.setup_trading_approvals())
            print(f"  approvals tx: {handle}")
        book = await tm.run("order book", client.get_order_book(asset_id=asset))
        print(f"  book: tick {book.tick_size}, min size {book.min_order_size}")
        if args.check:
            print("--check: stopping before any order")
            return

        res = await tm.run("place post-only BUY", client.place_limit_order(
            asset_id=asset, side="BUY", price=book.tick_size, size=book.min_order_size, post_only=True,
            builder_code=os.environ.get("BUILDER_CODE") or None))
        if not getattr(res, "ok", False):
            raise SystemExit(f"order rejected: {getattr(res, 'message', res)}")
        oid = res.order_id
        order = await tm.run("read order back", client.get_order(order_id=oid))
        print(f"  order status: {order.status}")
        cx = await tm.run("cancel", client.cancel_order(order_id=oid))
        print(f"  canceled: {cx.canceled}  not_canceled: {cx.not_canceled}")
    finally:
        await client.close()

    print("\nlatency summary (ms):")
    for label, ms in tm.rows:
        print(f"  {label:<28} {ms:8.1f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="stop before placing an order")
    ap.add_argument("--setup-approvals", action="store_true", help="send the trading approval transactions")
    asyncio.run(main(ap.parse_args()))
