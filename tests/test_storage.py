from portfolio import default_portfolio
from storage import load_portfolio, save_portfolio

def test_sqlite_round_trip(tmp_path):
    path = tmp_path / "portfolio.sqlite"
    holdings = default_portfolio()
    holdings.loc[0, "quantity"] = 1.25
    save_portfolio(holdings, 321.0, path)
    loaded, cash = load_portfolio(path)
    assert loaded.loc[0, "quantity"] == 1.25
    assert cash == 321.0
    assert list(loaded.columns) == list(holdings.columns)
