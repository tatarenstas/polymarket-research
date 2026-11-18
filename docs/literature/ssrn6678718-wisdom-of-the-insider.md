# Wisdom of the Crowd or Wisdom of the Insider? Insider Trading on Prediction Markets

- **SSRN:** [6678718](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6678718). Citation
  date 29 Apr 2026; one listing shows "2026-03". A working paper in empirical finance on
  market microstructure and informed trading.
  - The author's site lists the title as "The Wisdom of the Crowd or the Wisdom of Insiders?",
    so a slightly different title may exist.
- **Author:** Siyang Liu. A personal site describes the author as a Finance PhD student at
  UBC Sauder; affiliation not confirmed from the paper.
- **Code/data:** none found.
- **Read: NOT the full text.** SSRN blocked automated access behind a bot check, which was not
  bypassed. The author's site links only to SSRN. This note uses:
  - **[ABS]** abstract fragments surfaced by search engines;
  - **[HEC]** Bock & Guenthoer, *Detecting Informed Trading Before Resolution* (HEC Paris MIF
    research paper, 1 Jun 2026). It summarises Liu's numbers (§3.1.2–3.1.3) and gives a
    replication spec (§4.4.2, App. D.2). HEC says Liu fixes the signals and the
    aggregation rule **but not the per-signal thresholds**, so HEC's quartile cuts are
    HEC's own.

  Sample period, market counts, the way market makers are identified, matching rules, test
  statistics and tables were not seen.

## Question

Is Polymarket's accuracy the wisdom of a crowd, or partly the information of insiders? Who
earns the profits, who pays for insider information, and how do insiders organise on-chain?
[ABS]

## Data

- **Venue:** Polymarket, full on-chain transparency [ABS]. The period, size and contract era
  are not seen.
- **Detection eligibility (HEC):** (wallet, market) pairs where the wallet **won** (positive
  realised PnL on the resolved side) with ≥ $1,000 taker-side volume. Within-market
  references are used when there are ≥ 10 eligible winners.
- **Fund flows:** on-chain USDC flows traced via Etherscan and Relay.link (a cross-chain
  bridge) to link wallets that withdraw to a common non-exchange address [HEC, ABS].
- **Market makers and "information-clean" control markets:** both are mentioned [ABS]; how
  they are constructed is not seen.

## Methods

- **Five-fingerprint behavioural classifier** [HEC]. A pair is flagged when **≥ 4 of 5**
  fire; a wallet is flagged if any of its pairs is.

  | Fingerprint | HEC's operationalisation |
  | --- | --- |
  | Directional conviction | Top quartile of one-sidedness among the market's winners |
  | Favourable (low-VWAP) entry | Bottom quartile of VWAP per winning token |
  | Young or single-purpose wallet | Days from first on-chain activity to first trade in the market, bottom quartile globally |
  | Focus on few markets | Count of distinct markets ever traded, bottom quartile globally |
  | Large realised profit | Top quartile among the market's winners |

- **Sybil-cluster propagation** [ABS, HEC]. Wallets that send winnings to the same
  non-exchange withdrawal address are linked, and flags spread across the cluster.
- **Profit attribution** [ABS]. Realised winnings are decomposed by trader group (insiders,
  market makers, others) against each group's participation share.
- **Adverse-selection test** [ABS]. Market-maker profit per dollar is compared between
  markets flagged as compromised and matched information-clean markets, framed by Kyle
  (1985) and Glosten–Milgrom (1985).

## Findings

- **Profit concentration.** Realised profits are "extremely concentrated" in two
  economically distinct groups, **insiders and market makers**. Both take a share of winners'
  profit far above their share of participation [ABS].
- **Insider prevalence** [HEC, citing Liu]. 518 markets have at least one detected insider.
  Flagged wallets are **0.08% of participants** but take **7.1% of total winning profits**.
- **Who pays.** In compromised markets, market makers earn **18.5¢ less per dollar of
  volume** than in matched clean markets [HEC, citing Liu]. [ABS] calls this "substantially
  more" lost per dollar, consistent with Kyle–Glosten adverse selection.
- **Sybil organisation.** Insider activity runs through clusters in which one operator
  controls several accounts that send winnings to a single non-exchange withdrawal address,
  which the paper reads as deliberate concealment [ABS].
  - In the largest cluster, **37 of 43** Iran-strike insider wallets withdrew to one
    counterparty, which received **$2.08M** in total [HEC, citing Liu].
- **Conclusion.** Some of Polymarket's accuracy reflects insider information, and the rents
  are paid largely out of market-maker profits [ABS].
- **Replication by HEC** (not Liu's own result). With HEC's quartile thresholds, the
  behavioural scan flags 3,643 wallets and 4,119 pairs, out of 1.70M wallets and 16.75M
  pairs. It caught two of five documented cases, one of them a newly created single-purpose
  account.

## Reusable definitions

- The five fingerprints and the ≥ 4-of-5 rule.
- The eligible pool: winning pairs with ≥ $1,000 taker volume.
- The Sybil cluster as a shared non-exchange withdrawal destination.
- "Compromised" versus "information-clean" matched markets.
- Market-maker PnL per dollar of volume as the measure of adverse selection.

## Stated limitations

Not seen (abstract only). HEC notes that the thresholds are unspecified in the original.

## Critical assessment

These points come from the abstract and HEC's description, not the full text.

- **Selected on winning.** Only winning pairs are eligible, and high profit is one of the
  fingerprints. "Insiders capture 7.1% of winning profit" is therefore partly mechanical.
  The informative comparison would be against equally profiled wallets that lost. Young
  wallet, few markets and conviction also describe lucky one-off gamblers.
- **The market-maker test may be confounded.** Markets with an insider tend to be those with
  sharp, discrete information events. Market makers lose there to everyone who reacts to
  the news, not only insiders. Whether the matching controls for jumps and volatility is
  unknown.
- **The Sybil heuristic can merge unrelated users.** A shared non-exchange destination can be
  a bridge, router, OTC desk or custodial service. Relay.link is itself a bridge. Without
  excluding contract or service addresses, clusters can join unrelated users, and flags then
  spread to them.
- **Market makers are not defined** in the material seen. On Polymarket "maker" is a fill
  role, not an identity. An identity-level classification is needed.
- **Thresholds unspecified** (per HEC), which limits reproducibility.
- **Trust:**
  - profit concentration in insiders and market makers: **low–medium** (abstract only;
    partly mechanical);
  - 0.08% of wallets / 7.1% of winning profit: **low–medium** (secondhand; definition-
    dependent);
  - market makers pay (−18.5¢ per $): **medium** (plausible mechanism; matching unseen);
  - Sybil clusters (37/43 to one counterparty, $2.08M): **medium** (strong if the
    counterparty is a private address, weak if it is a shared service; unverifiable here).

## Directions it opens

- Run the full-population maker PnL decomposition. Measure liquidity providers' PnL per
  dollar around price jumps, split into jumps preceded by abnormal flow from flagged wallets
  and jumps that are not.
- Build a withdrawal-graph entity resolver from USDC/pUSD transfers, bridge calls and
  funding sources. Maintain a curated exclusion list of exchange, bridge and router contracts
  to avoid false merges.
- Re-run the fingerprints including losing pairs, and report precision against price-implied
  win probabilities rather than raw wins.
- Track wallet age at first trade and single-market usage as a live monitoring feature. Test
  in real time whether fresh-wallet flow predicts the next price move.
- Compare spreads and depth in at-risk categories before and after insider-flagged episodes,
  as a direct test of market makers widening quotes to protect against adverse selection.
