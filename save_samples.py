#!/usr/bin/env python3
"""Save representative CSV samples for each major API category."""
import os
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import rqdatac

rqdatac.init()
OUT = "/data/ricecta/data_samples"
os.makedirs(OUT, exist_ok=True)


def save(name, df):
    path = os.path.join(OUT, name + ".csv")
    if isinstance(df, pd.DataFrame):
        df.to_csv(path)
    else:
        pd.Series(df).to_csv(path)
    print("  saved " + name + ": " + str(df.shape))


# 1. Daily futures price (dominant contract)
for u in ["C", "M", "CU", "AU", "RB", "SC", "CF", "TA", "TF"]:
    try:
        dom = rqdatac.futures.get_dominant(u, start_date="20240115", end_date="20240120")
        contract = dom.iloc[-1]
        df = rqdatac.get_price(contract, start_date="20240115", end_date="20240131", frequency="1d", fields=["open", "high", "low", "close", "volume"])
        save("futures_daily_" + u + "_" + contract, df)
    except Exception as e:
        print("  FAIL " + u + ": " + str(e)[:80])

# 2. Continuous price
for u in ["CU", "AU", "CF"]:
    try:
        df = rqdatac.futures.get_dominant_price(u + "88", start_date="20240101", end_date="20240131", frequency="1d")
        save("futures_continuous_" + u + "88", df)
    except Exception as e:
        print("  FAIL cont " + u + ": " + str(e)[:80])

# 3. 5-Minute price
try:
    dom = rqdatac.futures.get_dominant("CU", start_date="20240115", end_date="20240120")
    df = rqdatac.get_price(dom.iloc[-1], start_date="20240115", end_date="20240115", frequency="5m", fields=["open", "close", "volume"])
    save("futures_5minute_CU", df)
except Exception as e:
    print("  FAIL minute: " + str(e)[:80])

# 4. Tick (L5 orderbook)
try:
    dom = rqdatac.futures.get_dominant("CU", start_date="20240115", end_date="20240120")
    df = rqdatac.get_price(dom.iloc[-1], start_date="20240115 09:30:00", end_date="20240115 09:32:00", frequency="tick")
    save("futures_tick_CU", df.head(500))
except Exception as e:
    print("  FAIL tick: " + str(e)[:80])


# 5. Warehouse stocks
for u in ["CU", "AL", "AU", "AG", "RB", "RU", "NI", "SN"]:
    try:
        df = rqdatac.futures.get_warehouse_stocks(u, start_date="20240101", end_date="20240131")
        save("warehouse_" + u, df)
    except Exception as e:
        print("  FAIL wh " + u + ": " + str(e)[:80])

# 6. Roll yield
for u in ["CU", "AU", "CF", "TA"]:
    try:
        df = rqdatac.futures.get_roll_yield(u, start_date="20240101", end_date="20240131")
        save("roll_yield_" + u, df)
    except Exception as e:
        print("  FAIL ry " + u + ": " + str(e)[:80])

# 7. Member rank
for u in ["CU", "AU", "CF"]:
    try:
        df = rqdatac.futures.get_member_rank(u, trading_date="20240102", rank_by="volume")
        save("member_rank_" + u, df)
    except Exception as e:
        print("  FAIL mr " + u + ": " + str(e)[:80])

# 8. Trading parameters
for u in ["CU", "AU", "RB", "SC", "TF"]:
    try:
        dom = rqdatac.futures.get_dominant(u, start_date="20240115", end_date="20240120")
        df = rqdatac.futures.get_trading_parameters(dom.iloc[-1], start_date="20240101", end_date="20240110")
        save("trading_params_" + u, df)
    except Exception as e:
        print("  FAIL tp " + u + ": " + str(e)[:80])

# 9. Exchange daily
for u in ["CU", "AU", "CF"]:
    try:
        dom = rqdatac.futures.get_dominant(u, start_date="20240115", end_date="20240120")
        df = rqdatac.futures.get_exchange_daily(dom.iloc[-1], start_date="20240101", end_date="20240110")
        save("exchange_daily_" + u, df)
    except Exception as e:
        print("  FAIL ed " + u + ": " + str(e)[:80])

# 10. Ex factor
for u in ["CU", "AU", "RB", "SC", "CF"]:
    try:
        df = rqdatac.futures.get_ex_factor(u, start_date="20240101", end_date="20240110")
        save("ex_factor_" + u, df)
    except Exception as e:
        print("  FAIL ef " + u + ": " + str(e)[:80])

# 11. Contracts list
for u in ["CU", "AU", "CF", "SC", "TF"]:
    try:
        df = rqdatac.futures.get_contracts(u)
        save("contracts_" + u, df)
    except Exception as e:
        print("  FAIL ct " + u + ": " + str(e)[:80])

# 12. Contract multiplier
for u in ["C", "M", "CU", "AU", "SC", "CF", "TA", "TF"]:
    try:
        df = rqdatac.futures.get_contract_multiplier(u, start_date="20240115", end_date="20240120")
        save("multiplier_" + u, df)
    except Exception as e:
        print("  FAIL cm " + u + ": " + str(e)[:80])


# 13. Stock indices
for code in ["000300.XSHG", "000905.XSHG", "000016.XSHG", "000852.XSHG"]:
    try:
        df = rqdatac.get_price(code, start_date="20240101", end_date="20240131", frequency="1d")
        save("index_" + code.replace(".", "_"), df)
    except Exception as e:
        print("  FAIL idx " + code + ": " + str(e)[:80])

# 14. Industry indices (申万)
for code in ["801010.INDX", "801020.INDX", "801030.INDX", "801040.INDX", "801050.INDX", "801053.INDX", "801055.INDX", "801950.INDX"]:
    try:
        df = rqdatac.get_price(code, start_date="20240101", end_date="20240131", frequency="1d")
        save("industry_" + code.replace(".", "_"), df)
    except Exception as e:
        print("  FAIL ind " + code + ": " + str(e)[:80])

# 15. Index PE/PB
try:
    df = rqdatac.index_indicator("000300.XSHG", start_date="20240101", end_date="20240131")
    save("index_indicator_HS300", df)
except Exception as e:
    print("  FAIL idxind: " + str(e)[:80])

# 16. Yield curve
try:
    df = rqdatac.get_yield_curve(start_date="20240102", end_date="20240110", country="cn")
    save("yield_curve_CN", df)
except Exception as e:
    print("  FAIL yc: " + str(e)[:80])

# 17. Shibor
try:
    df = rqdatac.get_interbank_offered_rate(start_date="20240101", end_date="20240110")
    save("shibor", df)
except Exception as e:
    print("  FAIL shibor: " + str(e)[:80])

# 18. FX
try:
    df = rqdatac.get_exchange_rate(start_date="20240101", end_date="20240110")
    save("fx_rates", df)
except Exception as e:
    print("  FAIL fx: " + str(e)[:80])

# 19. Gold spot
try:
    df = rqdatac.get_price("AU9999.SGEX", start_date="20240101", end_date="20240110", frequency="1d")
    save("spot_gold_AU9999", df)
except Exception as e:
    print("  FAIL gold: " + str(e)[:80])

# 20. Macro
try:
    df = rqdatac.econ.get_reserve_ratio(reserve_type="major", start_date="20230101", end_date="20240110")
    save("macro_rrr", df)
except Exception as e:
    print("  FAIL rrr: " + str(e)[:80])
try:
    df = rqdatac.econ.get_money_supply(start_date="20240101", end_date="20240110")
    save("macro_money_supply", df)
except Exception as e:
    print("  FAIL ms: " + str(e)[:80])
try:
    df = rqdatac.econ.get_factors(factors="工业品出厂价格指数PPI_当月同比_(上年同月=100)", start_date="20230101", end_date="20240101")
    save("macro_PPI", df)
except Exception as e:
    print("  FAIL ppi: " + str(e)[:80])
try:
    df = rqdatac.econ.get_factors(factors="居民消费价格指数CPI_当月同比_(上年同月=100)", start_date="20230101", end_date="20240101")
    save("macro_CPI", df)
except Exception as e:
    print("  FAIL cpi: " + str(e)[:80])


# 21. News
try:
    df = rqdatac.get_current_news(start_time="2024-01-15 09:00:00", end_time="2024-01-19 18:00:00")
    save("news_current", df.head(500))
except Exception as e:
    print("  FAIL news: " + str(e)[:80])

# 22. Instruments list
try:
    df = rqdatac.all_instruments(type="Future")
    save("instruments_Future", df.head(2000))
except Exception as e:
    print("  FAIL inst: " + str(e)[:80])

# 23. Index components
try:
    df = rqdatac.index_components("000300.XSHG", date="20240115")
    save("components_HS300", df)
except Exception as e:
    print("  FAIL comp: " + str(e)[:80])

# 24. Trading dates
try:
    df = rqdatac.get_trading_dates(start_date="20240101", end_date="20240131", market="cn")
    save("trading_dates", pd.Series(df, name="date"))
except Exception as e:
    print("  FAIL td: " + str(e)[:80])

# 25. Specific instruments metadata
for u in ["C2405", "CU2403", "SC2403", "CF2405", "TF2403"]:
    try:
        inst = rqdatac.instruments(u)
        d = {
            "order_book_id": inst.order_book_id,
            "symbol": inst.symbol,
            "exchange": inst.exchange,
            "underlying_symbol": inst.underlying_symbol,
            "margin_rate": inst.margin_rate,
            "contract_multiplier": inst.contract_multiplier,
            "trading_hours": inst.trading_hours,
            "listed_date": inst.listed_date,
            "maturity_date": inst.maturity_date,
            "round_lot": inst.round_lot,
        }
        pd.DataFrame([d]).to_csv(os.path.join(OUT, "instrument_" + u + ".csv"), index=False)
        print("  saved instrument_" + u)
    except Exception as e:
        print("  FAIL inst " + u + ": " + str(e)[:80])

print("\nDone. Files in " + OUT + ":")
print(str(len(os.listdir(OUT))) + " files")
