import pandas as pd
import pytest

from portfolio import default_portfolio, export_csv, import_csv, portfolio_snapshot, validate_portfolio

def test_default_targets_plus_cash_sum_to_100():
    holdings = default_portfolio()
    assert holdings["target_weight_pct"].sum() == pytest.approx(95.0)
    assert holdings["ticker"].is_unique
    assert validate_portfolio(holdings, 0) == []

def test_validation_rejects_incorrect_target_total():
    holdings = default_portfolio()
    holdings.loc[0, "target_weight_pct"] = 19.0
    assert any("sumar 95%" in error for error in validate_portfolio(holdings, 0))

def test_snapshot_counts_cash_and_positions():
    holdings = default_portfolio()
    holdings.loc[holdings["ticker"] == "VT", "quantity"] = 2
    view, summary = portfolio_snapshot(holdings, 100)
    assert summary["invested_known_usd"] == pytest.approx(260)
    assert summary["portfolio_value_known_usd"] == pytest.approx(360)
    assert len(view) == 13

def test_unknown_asset_with_quantity_marks_valuation_incomplete():
    holdings = default_portfolio()
    holdings.loc[0, ["ticker", "quantity"]] = ["NEW", 3]
    _, summary = portfolio_snapshot(holdings, 0)
    assert summary["valuation_incomplete"] is True

def test_csv_round_trip():
    holdings = default_portfolio()
    text = export_csv(holdings, 125.5)
    restored, cash = import_csv(text)
    assert restored["ticker"].tolist() == holdings["ticker"].tolist()
    assert restored["target_weight_pct"].tolist() == holdings["target_weight_pct"].tolist()
    assert restored["quantity"].tolist() == holdings["quantity"].tolist()
    assert restored["average_cost"].isna().all()
    assert cash == pytest.approx(125.5)
