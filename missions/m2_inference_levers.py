"""M2 — Inference Cost Levers: $/1M-token, batch x cache x cascade (deck §7).

Run: python missions/m2_inference_levers.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from missions._common import load_csv, num
from finops import pricing, sustainability

# $/1M tokens (input, output) — illustrative 2026.
MODEL_PRICES = {"small": (0.20, 0.40), "large": (3.00, 15.00)}


def run(verbose: bool = True) -> dict:
    rows = load_csv("token_usage.csv")
    base_cost = opt_cost = 0.0
    total_tokens = 0

    # Extension 4 tracking
    reasoning_requests = 0
    reasoning_cost = 0.0
    reasoning_wh = 0.0
    non_reasoning_wh = 0.0

    # Extension 3 tracking
    cached_reads_count = 0
    cache_hits_total = 0

    for r in rows:
        inp, out = int(num(r["input_tokens"])), int(num(r["output_tokens"]))
        cached = int(num(r["cached_input_tokens"]))
        is_batch = bool(int(num(r["is_batch"])))
        is_reasoning = bool(int(num(r["is_reasoning"])))
        total_tokens += inp + out

        if cached > 0:
            cached_reads_count += 1
            cache_hits_total += cached

        # BASELINE: naive deployment — everything on the large model, no cache, no batch
        lin, lout = MODEL_PRICES["large"]
        base_cost += pricing.request_cost(inp, out, lin, lout)

        # Extension 3: verify if cache is worth it before applying cache discount
        # Avg cached reads estimation
        apply_cache = cached if pricing.cache_is_worth_it(avg_cache_reads=2.5, write_cost_ratio=1.0) else 0

        # OPTIMIZED: cascade (route_tier), prompt caching, batch API
        pin, pout = MODEL_PRICES[r["route_tier"]]
        req_cost = pricing.request_cost(inp, out, pin, pout, cached_in=apply_cache, batch=is_batch)
        opt_cost += req_cost

        # Sustainability & Reasoning tracking
        wh = sustainability.wh_per_query(inp + out, is_reasoning=is_reasoning)
        if is_reasoning:
            reasoning_requests += 1
            reasoning_cost += req_cost
            reasoning_wh += wh
        else:
            non_reasoning_wh += wh

    base_pm = pricing.dollars_per_million(base_cost, total_tokens)
    opt_pm = pricing.dollars_per_million(opt_cost, total_tokens)
    savings_pct = (1 - opt_cost / base_cost) * 100 if base_cost else 0.0

    reasoning_pct_cost = (reasoning_cost / opt_cost * 100) if opt_cost else 0.0
    total_wh = reasoning_wh + non_reasoning_wh
    reasoning_pct_wh = (reasoning_wh / total_wh * 100) if total_wh else 0.0

    if verbose:
        print("== M2 Inference Cost Levers ==")
        print(f"requests={len(rows)}  tokens={total_tokens:,}")
        print(f"baseline  : ${base_cost:,.2f}/day   ${base_pm:.3f}/1M-token")
        print(f"optimized : ${opt_cost:,.2f}/day   ${opt_pm:.3f}/1M-token")
        print(f"savings   : {savings_pct:.1f}%  (cascade + caching + batch)")
        print(f"discount stack (batch + 100% cache): {pricing.discount_stack(batch=True, cache_hit_frac=1.0):.3f} of naive")

        print("\n-- Extension 3: Cache Economics Check --")
        print(f"Cache worthiness (2.5 avg reads vs 1.0 write ratio): {pricing.cache_is_worth_it(2.5, 1.0)}")

        print("\n-- Extension 4: Reasoning Budget Analysis --")
        print(f"Reasoning requests : {reasoning_requests}/{len(rows)} ({reasoning_requests/len(rows):.1%})")
        print(f"Reasoning cost     : ${reasoning_cost:,.2f}/day ({reasoning_pct_cost:.1f}% of optimized spend)")
        print(f"Reasoning energy   : {reasoning_wh/1000:.2f} kWh/day ({reasoning_pct_wh:.1f}% of total inference energy)")

    return {
        "baseline_daily": round(base_cost, 2), "optimized_daily": round(opt_cost, 2),
        "baseline_per_m": round(base_pm, 3), "optimized_per_m": round(opt_pm, 3),
        "savings_pct": round(savings_pct, 1), "total_tokens": total_tokens,
        "reasoning_cost_daily": round(reasoning_cost, 2),
        "reasoning_pct_cost": round(reasoning_pct_cost, 1),
        "reasoning_pct_energy": round(reasoning_pct_wh, 1),
    }


if __name__ == "__main__":
    run()

