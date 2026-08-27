import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from finops import pricing
from missions import m1_efficiency_audit, m2_inference_levers


def test_extension1_recommend_tier_advanced():
    # Standard behavior
    assert pricing.recommend_tier(2, True) == "spot"
    assert pricing.recommend_tier(24, False) == "reserved"
    assert pricing.recommend_tier(4, False) == "on_demand"

    # Enhanced behavior with high interruption risk GPU type (T4) and high duty cycle
    tier = pricing.recommend_tier(20, True, gpu_type="T4")
    assert tier == "reserved"


def test_extension2_mbu_rightsizing():
    res = m1_efficiency_audit.run(verbose=False)
    assert "rightsizing_recs" in res
    assert isinstance(res["rightsizing_recs"], list)


def test_extension3_cache_is_worth_it():
    # Break-even threshold is > 1.11 reads for 1.0 write ratio and 0.10 read discount
    assert pricing.cache_is_worth_it(avg_cache_reads=2.0, write_cost_ratio=1.0, read_discount=0.10) is True
    assert pricing.cache_is_worth_it(avg_cache_reads=0.5, write_cost_ratio=1.0, read_discount=0.10) is False


def test_extension4_reasoning_budget():
    res = m2_inference_levers.run(verbose=False)
    assert "reasoning_cost_daily" in res
    assert "reasoning_pct_energy" in res
    assert res["reasoning_cost_daily"] > 0
