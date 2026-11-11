from __future__ import annotations

import pandas as pd
import streamlit as st

from portfolio import COLUMNS, export_csv, import_csv, portfolio_snapshot, validate_portfolio
from storage import load_portfolio, save_portfolio

st.set_page_config(page_title="Portfolio Monitor", page_icon="📊", layout="wide")
st.title("Portfolio Monitor")
st.caption("V1 · Monitor local de cartera · USD")

if "holdings" not in st.session_state:
    st.session_state.holdings, st.session_state.cash_usd = load_portfolio()

holdings = st.session_state.holdings.copy()
cash_usd = float(st.session_state.cash_usd)

st.warning(
    "MODO DEMO: los precios son valores sintéticos ilustrativos, no cotizaciones actuales. "
    "No hay conexión a mercado ni a IBKR."
)

st.subheader("Cartera")
left, right = st.columns([3, 1])
with left:
    edited = st.data_editor(
        holdings,
        key="holdings_editor",
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "ticker": st.column_config.TextColumn("Ticker", required=True),
            "name": st.column_config.TextColumn("Nombre", required=True),
            "asset_type": st.column_config.SelectboxColumn(
                "Tipo", options=["ETF", "Stock", "Crypto", "Cash", "Other"], required=True
            ),
            "quantity": st.column_config.NumberColumn("Cantidad", min_value=0.0, step=0.01, format="%.6f"),
            "average_cost": st.column_config.NumberColumn("Costo promedio USD", min_value=0.0, step=0.01, format="%.2f"),
            "target_weight_pct": st.column_config.NumberColumn("Objetivo %", min_value=0.0, max_value=100.0, step=0.5, format="%.2f"),
        },
    )
with right:
    st.metric("Efectivo USD", f"$ {cash_usd:,.2f}")
    new_cash = st.number_input("Editar efectivo USD", min_value=0.0, value=cash_usd, step=100.0)
    st.caption("Los pesos objetivo son independientes de las posiciones reales.")
    if st.button("Guardar cartera", type="primary", use_container_width=True):
        errors = validate_portfolio(edited, new_cash)
        if errors:
            for error in errors:
                st.error(error)
        else:
            normalized = edited.copy()
            normalized["ticker"] = normalized["ticker"].astype(str).str.strip().str.upper()
            normalized["quantity"] = pd.to_numeric(normalized["quantity"], errors="coerce")
            normalized["average_cost"] = pd.to_numeric(normalized["average_cost"], errors="coerce")
            normalized["target_weight_pct"] = pd.to_numeric(normalized["target_weight_pct"], errors="coerce")
            save_portfolio(normalized, new_cash)
            st.session_state.holdings = normalized
            st.session_state.cash_usd = new_cash
            st.success("Cartera guardada localmente.")
            st.rerun()

st.divider()
view, summary = portfolio_snapshot(holdings, cash_usd)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Valor conocido", f"$ {summary['portfolio_value_known_usd']:,.2f}")
m2.metric("Invertido", f"$ {summary['invested_known_usd']:,.2f}")
m3.metric("Efectivo", f"$ {summary['cash_usd']:,.2f}")
m4.metric("Instrumentos", summary["position_count"])

if summary["valuation_incomplete"]:
    st.warning("La valoración está incompleta: hay posiciones con cantidad mayor a cero y sin precio demo.")
else:
    st.caption("La valoración usa exclusivamente los precios sintéticos de demostración.")

st.subheader("Asignación actual")
allocation_view = pd.concat([view, pd.DataFrame([summary["cash_row"]])], ignore_index=True)
display = allocation_view[["ticker", "name", "quantity", "reference_price", "market_value_usd", "actual_weight_pct", "target_weight_pct", "price_source"]].copy()
display.columns = ["Ticker", "Nombre", "Cantidad", "Precio demo USD", "Valor mercado USD", "Peso actual %", "Objetivo %", "Fuente"]
st.dataframe(display, use_container_width=True, hide_index=True)
st.caption("Los porcentajes actuales son aproximados mientras se use el modo demo; no representan datos de mercado.")

st.subheader("Respaldo CSV")
csv_data = export_csv(holdings, cash_usd)
st.download_button(
    "Exportar cartera CSV", data=csv_data, file_name="portfolio_backup.csv",
    mime="text/csv", use_container_width=False,
)
uploaded = st.file_uploader("Importar respaldo CSV", type=["csv"])
if uploaded is not None and st.button("Validar e importar CSV"):
    try:
        imported, imported_cash = import_csv(uploaded.getvalue().decode("utf-8-sig"))
        save_portfolio(imported, imported_cash)
        st.session_state.holdings = imported
        st.session_state.cash_usd = imported_cash
        st.success("Respaldo importado y guardado.")
        st.rerun()
    except (ValueError, UnicodeDecodeError, pd.errors.ParserError) as exc:
        st.error(f"No se pudo importar: {exc}")

with st.expander("Estado y límites de esta versión"):
    st.write("- Persistencia local mediante SQLite.")
    st.write("- Precios sintéticos; no se consultan proveedores externos.")
    st.write("- Sin conexión a IBKR y sin permisos ni funciones de trading.")
    st.write("- HH52 y ATR20W se incorporarán en una etapa posterior.")
