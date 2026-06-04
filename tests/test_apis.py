#!/usr/bin/env python3
"""Test all RQData free APIs and collect example data for our target futures.

Underlyings to test (from TODO.md):
- DCE:   C, M, Y, P, V, J, JD, I
- SHFE:  CU, AL, AU, AG, RB, RU, NI, SN
- INE:   SC
- CZCE:  CF, SR, TA, MA, SA
- CFFEX: TF
"""
import os
import json
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import rqdatac
import rqdatac_fund  # noqa: F401  (extend with fund module)

rqdatac.init()

OUT = "/data/ricecta/data_samples"
os.makedirs(OUT, exist_ok=True)

UNDERLYINGS = ["C", "M", "Y", "P", "V", "J", "JD", "I",
               "CU", "AL", "AU", "AG", "RB", "RU", "NI", "SN",
               "SC",
               "CF", "SR", "TA", "MA", "SA",
               "TF"]

results = {}

def test_api(name, fn, *args, **kwargs):
    try:
        df = fn(*args, **kwargs)
        if isinstance(df, pd.DataFrame):
            sample = df.head(3).to_dict(orient="records")
            shape = list(df.shape)
        elif isinstance(df, pd.Series):
            sample = df.head(3).to_dict()
            shape = [len(df)]
        else:
            sample = str(df)[:300]
            shape = "scalar"
        results[name] = ("OK", "", sample, shape)
        print(f"  [OK] {name}: shape={shape}")
    except Exception as e:
        results[name] = ("FAIL", str(e)[:200], None, None)
        print(f"  [FAIL] {name}: {str(e)[:120]}")


print("=" * 80)
print("1) USER & QUOTA INFO")
print("=" * 80)
test_api("rqdatac.info", rqdatac.info)
test_api("user.get_quota", rqdatac.user.get_quota)


print("\n" + "=" * 80)
print("2) TRADING CALENDAR")
print("=" * 80)
test_api("get_trading_dates", rqdatac.get_trading_dates, start_date="20240101", end_date="20240131", market="cn")
test_api("get_previous_trading_date", rqdatac.get_previous_trading_date, date="20240115", market="cn")
test_api("get_next_trading_date", rqdatac.get_next_trading_date, date="20240115", market="cn")
test_api("is_trading_date", rqdatac.is_trading_date, date="20240115", market="cn")
test_api("get_latest_trading_date", rqdatac.get_latest_trading_date, market="cn")


print("\n" + "=" * 80)
print("3) INSTRUMENTS / CONTRACTS - per underlying")
print("=" * 80)
test_api("all_instruments Future (total list)", rqdatac.all_instruments, type="Future")
test_api("instruments CU2501", rqdatac.instruments, "CU2501")
for u in UNDERLYINGS:
    test_api("futures.get_contracts " + u, rqdatac.futures.get_contracts, u)
    test_api("futures.get_dominant " + u + " (recent)", rqdatac.futures.get_dominant, u, start_date="20240115", end_date="20240120")
    test_api("futures.get_contract_multiplier " + u, rqdatac.futures.get_contract_multiplier, u, start_date="20240115", end_date="20240120")
    test_api("futures.get_ex_factor " + u, rqdatac.futures.get_ex_factor, u, start_date="20240101", end_date="20240110")


print("\n" + "=" * 80)
print("4) PRICE (DAILY) - per underlying (using dominant contract)")
print("=" * 80)
for u in UNDERLYINGS:
    try:
        dom = rqdatac.futures.get_dominant(u, start_date="20240115", end_date="20240120")
        if isinstance(dom, pd.Series) and len(dom) > 0:
            contract = dom.iloc[-1]
        else:
            contract = u
        test_api("get_price " + u + " (" + contract + ")", rqdatac.get_price, contract, start_date="20240115", end_date="20240131", frequency="1d", fields=["open", "high", "low", "close", "volume"])
    except Exception as e:
        print("  [FAIL] get_price " + u + ": " + str(e)[:120])
    # also continuous
    test_api("futures.get_dominant_price " + u + "88", rqdatac.futures.get_dominant_price, u + "88", start_date="20240101", end_date="20240131", frequency="1d", fields=["open", "close", "volume"])


print("\n" + "=" * 80)
print("5) FUTURES FEATURES - roll yield, basis, warehouse, params, member, exchange_daily")
print("=" * 80)
for u in UNDERLYINGS:
    test_api("futures.get_roll_yield " + u, rqdatac.futures.get_roll_yield, u, start_date="20240101", end_date="20240131")
    test_api("futures.get_warehouse_stocks " + u, rqdatac.futures.get_warehouse_stocks, u, start_date="20240101", end_date="20240131")
    test_api("futures.get_member_rank " + u, rqdatac.futures.get_member_rank, u, trading_date="20240102", rank_by="volume")
    test_api("futures.get_trading_parameters " + u, rqdatac.futures.get_trading_parameters, u, start_date="20240101", end_date="20240110")
    test_api("futures.get_exchange_daily " + u, rqdatac.futures.get_exchange_daily, u, start_date="20240101", end_date="20240110")


print("\n" + "=" * 80)
print("6) MINUTE PRICE")
print("=" * 80)
# one underlying from each exchange, 1 day
for u in ["C", "CU", "SC", "CF", "TF"]:
    try:
        dom = rqdatac.futures.get_dominant(u, start_date="20240115", end_date="20240120")
        contract = dom.iloc[-1] if isinstance(dom, pd.Series) and len(dom) > 0 else u
        test_api("get_price " + u + " 1m", rqdatac.get_price, contract, start_date="20240115", end_date="20240115", frequency="1m", fields=["open", "close", "volume"])
    except Exception as e:
        print("  [FAIL] 1m " + u + ": " + str(e)[:120])


print("\n" + "=" * 80)
print("7) INDICES - HS300, Wind A, Shenwan industry 801xxx, 申万一级")
print("=" * 80)
test_api("get_price 000300.XSHG (HS300)", rqdatac.get_price, "000300.XSHG", start_date="20240101", end_date="20240110", frequency="1d")
test_api("get_price 000905.XSHG (CSI500)", rqdatac.get_price, "000905.XSHG", start_date="20240101", end_date="20240110", frequency="1d")
test_api("get_price 000016.XSHG (SSE50)", rqdatac.get_price, "000016.XSHG", start_date="20240101", end_date="20240110", frequency="1d")
test_api("get_price 000852.XSHG (CSI1000)", rqdatac.get_price, "000852.XSHG", start_date="20240101", end_date="20240110", frequency="1d")
test_api("index_components 000300.XSHG", rqdatac.index_components, "000300.XSHG", date="20240115")
test_api("index_components 000905.XSHG", rqdatac.index_components, "000905.XSHG", date="20240115")
test_api("get_price 801010.INDX (申万农林牧渔)", rqdatac.get_price, "801010.INDX", start_date="20240101", end_date="20240110", frequency="1d")
test_api("get_price 801040.INDX (申万有色金属)", rqdatac.get_price, "801040.INDX", start_date="20240101", end_date="20240110", frequency="1d")
test_api("get_price 801120.INDX (申万食品饮料)", rqdatac.get_price, "801120.INDX", start_date="20240101", end_date="20240110", frequency="1d")
test_api("get_price 801180.INDX (申万房地产)", rqdatac.get_price, "801180.INDX", start_date="20240101", end_date="20240110", frequency="1d")
test_api("index_indicator 000300.XSHG (PE/PB)", rqdatac.index_indicator, "000300.XSHG", start_date="20240101", end_date="20240110")
test_api("index_weights 000300.XSHG", rqdatac.index_weights, "000300.XSHG", date="20240115")


print("\n" + "=" * 80)
print("8) SPOT (Shanghai Gold Exchange) + Repo / Rates (Shibor)")
print("=" * 80)
test_api("get_price AU9999.SGEX (gold spot)", rqdatac.get_price, "AU9999.SGEX", start_date="20240101", end_date="20240110", frequency="1d")
test_api("get_price AG9999.SGEX (silver spot)", rqdatac.get_price, "AG9999.SGEX", start_date="20240101", end_date="20240110", frequency="1d")
test_api("get_price PT9999.SGEX (platinum spot)", rqdatac.get_price, "PT9999.SGEX", start_date="20240101", end_date="20240110", frequency="1d")
test_api("get_spot_benchmark_price AU9999.SGEX", rqdatac.get_spot_benchmark_price, "AU9999.SGEX", start_date="20240101", end_date="20240110")
test_api("get_interbank_offered_rate (Shibor)", rqdatac.get_interbank_offered_rate, start_date="20240101", end_date="20240110")
test_api("get_yield_curve (CGB)", rqdatac.get_yield_curve, start_date="20240102", end_date="20240110", country="cn")


print("\n" + "=" * 80)
print("9) FX (exchange rate)")
print("=" * 80)
test_api("get_exchange_rate HKDCNY", rqdatac.get_exchange_rate, start_date="20240101", end_date="20240110")


print("\n" + "=" * 80)
print("10) MACRO (econ)")
print("=" * 80)
test_api("econ.get_reserve_ratio (RRR)", rqdatac.econ.get_reserve_ratio, reserve_type="major", start_date="20230101", end_date="20240110")
test_api("econ.get_money_supply (M0/M1/M2)", rqdatac.econ.get_money_supply, start_date="20240101", end_date="20240110")
# try a few standard factor names
for fac in ["工业品出厂价格指数PPI_当月同比_(上年同月=100)", "居民消费价格指数CPI_当月同比_(上年同月=100)", "制造业PMI_指数_(季节调整)", "GDP_不变价_当季同比"]:
    test_api("econ.get_factors " + fac[:8] + "...", rqdatac.econ.get_factors, factors=fac, start_date="20230101", end_date="20240101")


print("\n" + "=" * 80)
print("11) ALTERNATIVE DATA - NEWS / consensus")
print("=" * 80)
test_api("get_current_news (n=5)", rqdatac.get_current_news, n=5)
test_api("get_current_news (date range)", rqdatac.get_current_news, start_time="2024-01-15 09:00:00", end_time="2024-01-19 18:00:00")
test_api("consensus.get_indicator 000001.XSHE FY2024", rqdatac.consensus.get_indicator, "000001.XSHE", fiscal_year="2024")
test_api("all_consensus_industries", rqdatac.all_consensus_industries)


print("\n" + "=" * 80)
print("12) CONCRETE-CONTRACT TESTS for trading_params / exchange_daily / 1m")
print("=" * 80)
for u in ["C", "M", "Y", "P", "V", "J", "JD", "I", "CU", "AL", "AU", "AG", "RB", "RU", "NI", "SN", "SC", "CF", "SR", "TA", "MA", "SA", "TF"]:
    try:
        dom = rqdatac.futures.get_dominant(u, start_date="20240115", end_date="20240120")
        contract = dom.iloc[-1] if isinstance(dom, pd.Series) and len(dom) > 0 else u
        test_api("futures.get_trading_parameters " + u + " (" + contract + ")", rqdatac.futures.get_trading_parameters, contract, start_date="20240101", end_date="20240110")
        test_api("futures.get_exchange_daily " + u + " (" + contract + ")", rqdatac.futures.get_exchange_daily, contract, start_date="20240101", end_date="20240110")
        test_api("futures.get_basis " + u + " (" + contract + ")", rqdatac.futures.get_basis, contract, start_date="20240101", end_date="20240110")
    except Exception as e:
        print("  [FAIL] " + u + ": " + str(e)[:100])



print("\n" + "=" * 80)
print("12) SAVE RESULTS")
print("=" * 80)
out_path = os.path.join(OUT, "api_test_results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({k: [v[0], v[1], str(v[2]), v[3]] for k, v in results.items()}, f, ensure_ascii=False, indent=2, default=str)
print("Saved: " + out_path)
print("Total APIs tested: " + str(len(results)))
print("OK:   " + str(sum(1 for v in results.values() if v[0]=='OK')))
print("FAIL: " + str(sum(1 for v in results.values() if v[0]=='FAIL')))
