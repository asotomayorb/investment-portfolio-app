"""Portfolio defaults, validation, calculations and CSV interchange."""
from __future__ import annotations

from io import StringIO
import pandas as pd

COLUMNS = ["ticker", "name", "asset_type", "quantity", "average_cost", "target_weight_pct"]

DEFAULT_HOLDINGS = [
    ("VT", "Vanguard Total World Stock ETF", "ETF", 20.0),
    ("SMH", "VanEck Semiconductor ETF", "ETF", 15.0),
    ("BTCUSD", "Bitcoin", "Crypto", 10.0),
    ("INDA", "iShares MSCI India ETF", "ETF", 10.0),
    ("MSFT", "Microsoft", "Stock", 5.0),
    ("NVDA", "NVIDIA", "Stock", 5.0),
    ("AVGO", "Broadcom", "Stock", 5.0),
    ("GLD", "SPDR Gold Shares", "ETF", 5.0),
    ("URA", "Global X Uranium ETF", "ETF", 5.0),
    ("XLE", "Energy Select Sector SPDR Fund", "ETF", 4.0),
    ("VHT", "Vanguard Health Care ETF", "ETF", 4.0),
    ("PLTR", "Palantir", "Stock", 4.0),
    ("QQQ", "Invesco QQQ Trust", "ETF", 3.0),
]

# Illustrative values solely to exercise the interface. Never treat as market quotes.
DEMO_PRICES = {
    "VT": 130.0, "SMH": 300.0, "BTCUSD": 65000.0, "INDA": 55.0,
    "MSFT": 500.0, "NVDA": 180.0, "AVGO": 350.0, "GLD": 400.0,
    "URA": 35.0, "XLE": 90.0, "VHT": 300.0, "PLTR": 150.0, "QQQ": 600.0,
}

def default_portfolio() -> pd.DataFrame:
    rows = [
        {"ticker": ticker, "name": name, "asset_type": kind,
         "quantity": 0.0, "average_cost": None, "target_weight_pct": weight}
        for ticker, name, kind, weight in DEFAULT_HOLDINGS
    ]
    return pd.DataFrame(rows, columns=COLUMNS)

def validate_portfolio(holdings: pd.DataFrame, cash_usd: float, require_targets_total: bool = True) -> list[str]:
    errors: list[str] = []
    missing = [c for c in COLUMNS if c not in holdings.columns]
    if missing:
        return [f"Faltan columnas: {', '.join(missing)}"]
    clean = holdings.copy()
    clean["ticker"] = clean["ticker"].fillna("").astype(str).str.strip().str.upper()
    if (clean["ticker"] == "").any():
        errors.append("Cada instrumento debe tener un ticker.")
    if clean["ticker"].duplicated().any():
        errors.append("No puede haber tickers duplicados.")
    for col, label in [("quantity", "cantidad"), ("target_weight_pct", "peso objetivo")]:
        values = pd.to_numeric(clean[col], errors="coerce")
        if values.isna().any() or (values < 0).any():
            errors.append(f"La {label} debe ser un número mayor o igual a cero.")
    costs = pd.to_numeric(clean["average_cost"], errors="coerce")
    if (costs.dropna() < 0).any():
        errors.append("El costo promedio no puede ser negativo.")
    try:
        if pd.isna(cash_usd) or float(cash_usd) < 0:
            errors.append("El efectivo debe ser un número mayor o igual a cero.")
    except (TypeError, ValueError):
        errors.append("El efectivo debe ser un número válido.")
    if require_targets_total:
        total = pd.to_numeric(clean["target_weight_pct"], errors="coerce").sum(min_count=1)
        if pd.notna(total) and abs(float(total) - 100.0) > 0.01:
            errors.append(f"Los pesos objetivo deben sumar 100% (actual: {total:.2f}%).")
    return errors

def portfolio_snapshot(holdings: pd.DataFrame, cash_usd: float) -> tuple[pd.DataFrame, dict]:
    view = holdings.copy()
    view["ticker"] = view["ticker"].astype(str).str.strip().str.upper()
    view["reference_price"] = view["ticker"].map(DEMO_PRICES)
    view["price_source"] = view["reference_price"].apply(
        lambda value: "DEMO sintético" if pd.notna(value) else "Sin dato"
    )
    view["market_value_usd"] = pd.to_numeric(view["quantity"], errors="coerce") * view["reference_price"]
    priced = view["reference_price"].notna()
    incomplete = bool((~priced & (pd.to_numeric(view["quantity"], errors="coerce").fillna(0) > 0)).any())
    invested_known = float(view["market_value_usd"].fillna(0).sum())
    total_known = invested_known + float(cash_usd)
    view["actual_weight_pct"] = (view["market_value_usd"] / total_known * 100) if total_known > 0 else 0.0
    cash_row = {
        "ticker": "CASH", "name": "Efectivo USD", "asset_type": "Cash",
        "quantity": float(cash_usd), "reference_price": 1.0,
        "market_value_usd": float(cash_usd),
        "actual_weight_pct": (float(cash_usd) / total_known * 100) if total_known > 0 else 0.0,
        "target_weight_pct": 5.0, "price_source": "Saldo ingresado por usuario",
    }
    summary = {
        "cash_usd": float(cash_usd),
        "invested_known_usd": invested_known,
        "portfolio_value_known_usd": total_known,
        "valuation_incomplete": incomplete,
        "priced_positions": int(priced.sum()),
        "position_count": len(view),
    }
    return view, {**summary, "cash_row": cash_row}

def export_csv(holdings: pd.DataFrame, cash_usd: float) -> str:
    out = holdings[COLUMNS].copy()
    out.insert(0, "cash_usd", "")
    if not out.empty:
        out.loc[out.index[0], "cash_usd"] = float(cash_usd)
    return out.to_csv(index=False)

def import_csv(content: str) -> tuple[pd.DataFrame, float]:
    frame = pd.read_csv(StringIO(content))
    required = set(COLUMNS)
    if not required.issubset(frame.columns):
        raise ValueError(f"El CSV debe incluir: {', '.join(COLUMNS)}")
    cash = pd.to_numeric(frame.get("cash_usd", pd.Series([0])), errors="coerce").dropna()
    cash_usd = float(cash.iloc[0]) if not cash.empty else 0.0
    result = frame[COLUMNS].copy()
    result["ticker"] = result["ticker"].fillna("").astype(str).str.strip().str.upper()
    result["quantity"] = pd.to_numeric(result["quantity"], errors="coerce")
    result["average_cost"] = pd.to_numeric(result["average_cost"], errors="coerce")
    result["target_weight_pct"] = pd.to_numeric(result["target_weight_pct"], errors="coerce")
    result["name"] = result["name"].fillna("").astype(str)
    result["asset_type"] = result["asset_type"].fillna("Other").astype(str)
    errors = validate_portfolio(result, cash_usd)
    if errors:
        raise ValueError(" ".join(errors))
    return result, cash_usd
