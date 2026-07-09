import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re
from pathlib import Path

# ── COLORS (Vista Hermosa brand palette) ──────────────────────────────────────
C_YELLOW = "#F5C318"
C_DARK   = "#1A1A1A"
C_GREEN  = "#2E6B2E"
C_WHITE  = "#FFFFFF"
C_LGRAY  = "#F7F7F7"
C_MGRAY  = "#E0E0E0"
C_RED    = "#C62828"

PROMO_SHEET_CSV = ("https://docs.google.com/spreadsheets/d/"
                   "11JOMw6xMH1eC6w-MO4RkWvcxWj_BYbQlJylxnvuZbYM/export?format=csv&gid=0")

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Vista Hermosa · WFM Dashboard",
                   layout="wide", initial_sidebar_state="collapsed")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  [data-testid="stAppViewContainer"] {{ background-color:{C_LGRAY}; }}
  [data-testid="stHeader"] {{ background-color:{C_DARK}; height:0; }}
  .block-container {{ padding:0 1.5rem 2rem; max-width:100%; }}
  div[data-testid="stVerticalBlock"] > div {{ gap:0.5rem; }}

  .vh-hdr {{ background:{C_DARK}; border-bottom:4px solid {C_YELLOW};
    padding:16px 28px; margin:0 -1.5rem 1.25rem;
    display:flex; align-items:center; justify-content:space-between; min-height:72px; }}
  .vh-hdr-left  {{ display:flex; align-items:center; gap:18px; }}
  .vh-hdr-title {{ color:{C_WHITE}; font-size:22px; font-weight:800;
                   letter-spacing:2px; margin:0; line-height:1.1; }}
  .vh-hdr-sub   {{ color:#00A862; font-size:13px; margin:4px 0 0;
                   letter-spacing:.5px; font-weight:600; }}
  .vh-hdr-badge {{ background:{C_YELLOW}; color:{C_DARK}; font-size:12px;
                   font-weight:700; padding:6px 14px; border-radius:4px; }}

  .filter-panel {{ background:{C_WHITE}; border:1px solid {C_MGRAY}; border-radius:8px;
                   padding:14px 14px 6px; }}
  .filter-title {{ font-size:11px; font-weight:700; color:#666; text-transform:uppercase;
                   letter-spacing:.6px; margin-bottom:10px;
                   border-left:3px solid {C_YELLOW}; padding-left:8px; }}

  .kpi-card {{ background:{C_WHITE}; border-radius:8px; padding:20px 16px;
               border-top:4px solid {C_YELLOW}; box-shadow:0 2px 6px rgba(0,0,0,.09);
               height:100%; text-align:center; overflow-wrap:anywhere; }}
  .kpi-row  {{ background:{C_LGRAY}; border-radius:10px; padding:16px 12px; margin-bottom:1rem; }}
  .kpi-lbl  {{ font-size:12px; font-weight:700; color:#888; text-transform:uppercase;
               letter-spacing:.5px; margin-bottom:8px; }}
  .kpi-val  {{ font-size:36px; font-weight:800; color:{C_DARK}; line-height:1; }}
  .kpi-sub  {{ font-size:13px; color:#999; margin-top:6px; }}
  .kpi-pos  {{ font-size:14px; font-weight:600; color:{C_GREEN}; margin-top:6px; }}
  .kpi-neg  {{ font-size:14px; font-weight:600; color:{C_RED}; margin-top:6px; }}

  .sec-hdr {{ font-size:18px; font-weight:800; color:{C_DARK}; letter-spacing:.5px;
              border-bottom:3px solid {C_YELLOW}; padding-bottom:8px;
              margin:1.5rem 0 1rem; text-align:center; }}

  .broker-card {{ background:{C_WHITE}; border-radius:8px; padding:20px;
                  border-top:4px solid {C_DARK}; box-shadow:0 1px 4px rgba(0,0,0,.07); }}
  .broker-name {{ font-size:14px; font-weight:800; color:{C_DARK}; margin-bottom:14px;
                  text-transform:uppercase; letter-spacing:1px; }}
  .broker-row  {{ display:flex; justify-content:space-between;
                  border-bottom:1px solid {C_MGRAY}; padding:7px 0; }}
  .broker-key  {{ font-size:12px; color:#666; }}
  .broker-val  {{ font-size:12px; font-weight:700; color:{C_DARK}; }}
  .broker-trend-pos {{ color:{C_GREEN}; font-weight:700; }}
  .broker-trend-neg {{ color:{C_RED}; font-weight:700; }}

  .stTabs [data-baseweb="tab-list"] {{ background:{C_DARK}; border-radius:6px 6px 0 0;
                                       gap:2px; padding:4px 6px 0; }}
  .stTabs [data-baseweb="tab"] {{ color:{C_WHITE}; border-radius:5px 5px 0 0;
                                  font-size:13px; font-weight:600; padding:8px 20px; }}
  .stTabs [aria-selected="true"] {{ background:{C_YELLOW} !important; color:{C_DARK} !important; }}
  .stTabs [data-baseweb="tab-panel"] {{ background:{C_LGRAY}; border-radius:0 0 8px 8px;
                                        padding:1rem 0 0; border:1px solid {C_MGRAY}; }}

  .oos-badge  {{ background:#FFEBEE; color:{C_RED}; font-size:10px;
                 font-weight:700; padding:2px 6px; border-radius:4px; }}
  .warn-badge {{ background:#FFF8E1; color:#F57F17; font-size:10px;
                 font-weight:700; padding:2px 6px; border-radius:4px; }}
  .ok-badge   {{ background:#E8F5E9; color:{C_GREEN}; font-size:10px;
                 font-weight:700; padding:2px 6px; border-radius:4px; }}
  .promo-badge {{ background:{C_YELLOW}; color:{C_DARK}; font-size:11px;
                  font-weight:700; padding:3px 8px; border-radius:4px; }}
</style>
""", unsafe_allow_html=True)

# ── DATA LOADING ──────────────────────────────────────────────────────────────
DATA = Path(__file__).parent

@st.cache_data(ttl=1800, show_spinner="Loading sales data…")
def load_data():
    sales  = pd.read_csv(DATA / "VH_WFM_Item_Sales_Combined.csv", encoding="utf-8-sig")
    stores = pd.read_csv(DATA / "dim_stores.csv", encoding="utf-8-sig")
    broker = pd.read_csv(DATA / "dim_broker_coverage.csv", encoding="utf-8-sig")
    bm     = pd.read_csv(DATA / "dim_basemaker_coverage.csv", encoding="utf-8-sig")

    sales["Week Ending"] = pd.to_datetime(sales["Week Ending"], format="%m/%d/%y")
    sales["Month_Year"]  = sales["Week Ending"].dt.strftime("%b %Y")

    for c in ["Net Sales", "Unit Sales", "Net Sales LY", "Unit Sales LY",
              "Gross Sales", "Return Sales", "Gross Units", "Return Units"]:
        sales[c] = pd.to_numeric(sales[c], errors="coerce").fillna(0)
    sales["Avg Net Retail Price"] = pd.to_numeric(sales["Avg Net Retail Price"], errors="coerce")

    # Store dims (rebuilt from WFM master store list + UNFI DC mapping)
    stores_sub = stores[["Store_Number", "WFM_Region", "UNFI_DC", "UNFI_Region",
                         "Status", "State", "City"]].drop_duplicates("Store_Number")
    sales["Store Number"] = pd.to_numeric(sales["Store Number"], errors="coerce")
    sales = sales.merge(stores_sub, left_on="Store Number",
                        right_on="Store_Number", how="left")
    sales["UNFI_DC"] = sales["UNFI_DC"].fillna("Unmapped")

    # Merchandiser flags — Final Touch by store name, Basemakers by store number / name
    ft_names = set(broker[broker["Broker"] == "Final Touch"]["Location_Name"]
                   .astype(str).str.strip().str.lower())
    bm_wfm = bm[bm["Account"] == "WFM"].copy()
    bm_wfm["_store_num"] = (bm_wfm["Store_Name"].str.extract(r"#(\d+)")[0].astype(float))
    bm_wfm_nums = set(bm_wfm["_store_num"].dropna())
    bm_names = set(bm[bm["Account"] != "WFM"]["Store_Name"].astype(str).str.strip().str.lower())

    sname = sales["Store Name"].astype(str).str.strip().str.lower()
    sales["Merchandiser"] = "Uncovered"
    sales.loc[sname.isin(ft_names), "Merchandiser"] = "Final Touch"
    sales.loc[sname.isin(bm_names), "Merchandiser"] = "Basemakers"
    sales.loc[sales["Store Number"].isin(bm_wfm_nums), "Merchandiser"] = "Basemakers"

    # Remove burritos (no meaningful sales in 2026)
    sales = sales[~sales["Item Description"].str.upper().str.startswith("BURRITO")]

    # WFM category names → VH names
    sales["Category"] = sales["Category"].replace(
        {"Flatbreads": "Tortillas", "Salty Snacks": "Totopos"})

    # Distributor rollup from DC
    west_dcs = {"aurora", "moreno", "gilroy", "rocklin", "ridgefield"}
    sales["Distributor"] = sales["UNFI_DC"].fillna("").apply(
        lambda x: "Rainforest/West" if any(w in str(x).lower() for w in west_dcs)
                  else ("UNFI East" if x and x != "Unmapped" else "Unknown"))

    open_store_count = int((stores["Status"] == "Open").sum())
    return sales, broker, bm, open_store_count

sales, broker_df, bm_df, OPEN_STORES = load_data()

@st.cache_data(ttl=300, show_spinner=False)
def load_promo_calendar():
    """Manual promo calendar maintained in the shared Google Sheet.
    Falls back to a local dim_promo_periods.csv if the sheet is unreachable."""
    df = None
    try:
        df = pd.read_csv(PROMO_SHEET_CSV)
    except Exception:
        local = DATA / "dim_promo_periods.csv"
        if local.exists():
            df = pd.read_csv(local, encoding="utf-8-sig")
    if df is None:
        return pd.DataFrame()
    df.columns = [str(c).strip() for c in df.columns]
    need = {"Promo_Name", "Start_Date", "End_Date", "UPC", "Status"}
    if not need.issubset(df.columns):
        return pd.DataFrame()
    df = df[df["Promo_Name"].notna()]
    df = df[~df["Promo_Name"].astype(str).str.upper().str.startswith("EXAMPLE")]
    df = df[~df["Promo_Name"].astype(str).str.startswith(("HOW THIS", "1.", "2.", "3.",
                                                          "4.", "5.", "6."))]
    df = df[df["Status"].isin(["Confirmed", "Live", "Completed"])]
    df["Start_Date"] = pd.to_datetime(df["Start_Date"], errors="coerce")
    df["End_Date"]   = pd.to_datetime(df["End_Date"], errors="coerce")
    df = df.dropna(subset=["Start_Date", "End_Date"])
    df["UPC"] = pd.to_numeric(df["UPC"], errors="coerce").astype("Int64")
    return df

promo_cal = load_promo_calendar()

# ── SHARED HELPERS ────────────────────────────────────────────────────────────
def velocity(df):
    """Avg units per selling store-SKU-week (units/store/SKU/wk)."""
    sell = df[df["Unit Sales"] > 0]
    if sell.empty:
        return 0.0
    denom = sell.groupby(["Store Name", "Item Description", "Week Ending"]).size().shape[0]
    return df["Unit Sales"].sum() / denom

def dollar_velocity(df):
    """Avg $ per selling store-SKU-week."""
    sell = df[df["Net Sales"] > 0]
    if sell.empty:
        return 0.0
    denom = sell.groupby(["Store Name", "Item Description", "Week Ending"]).size().shape[0]
    return df["Net Sales"].sum() / denom

def velocity_ly(df):
    """Prior-year unit velocity for the same weeks, from LY columns."""
    sell = df[df["Unit Sales LY"] > 0]
    if sell.empty:
        return 0.0
    denom = sell.groupby(["Store Name", "Item Description", "Week Ending"]).size().shape[0]
    return df["Unit Sales LY"].sum() / denom

def dollar_velocity_ly(df):
    sell = df[df["Net Sales LY"] > 0]
    if sell.empty:
        return 0.0
    denom = sell.groupby(["Store Name", "Item Description", "Week Ending"]).size().shape[0]
    return df["Net Sales LY"].sum() / denom

@st.cache_data
def weeks_since_sale(sales_df):
    max_wk = sales_df["Week Ending"].max()
    last = (sales_df[sales_df["Unit Sales"] > 0]
            .groupby(["Store Name", "Item Description"])["Week Ending"].max()
            .reset_index())
    last["Weeks Since Sale"] = ((max_wk - last["Week Ending"]).dt.days / 7).round(0).astype(int)
    return last[["Store Name", "Item Description", "Weeks Since Sale"]]

wks_since = weeks_since_sale(sales)

def is_stale(w):
    if w == "OOS":
        return True
    try:
        return float(w) > 2
    except Exception:
        return False

def delta_class(v): return "kpi-pos" if v >= 0 else "kpi-neg"
def arrow(v):       return "▲" if v >= 0 else "▼"

def render_filter_panel(container, prefix, show_comparison=False):
    """Render this page's filters in a right-hand panel. Returns dict of selections."""
    sel = {}
    with container:
        st.markdown('<div class="filter-title">FILTERS — THIS PAGE</div>',
                    unsafe_allow_html=True)
        week_opts = [pd.Timestamp(w).strftime("%m/%d/%y") for w in ALL_WEEKS]
        sel["weeks"] = st.multiselect("Week Ending", week_opts,
                                      default=week_opts[:4], key=f"{prefix}_weeks")
        month_opts = sorted(sales["Month_Year"].unique(),
                            key=lambda x: pd.to_datetime(x, format="%b %Y"), reverse=True)
        sel["months"] = st.multiselect("Month / Year", month_opts, key=f"{prefix}_months")
        sel["cat"] = st.multiselect(
            "Category", sorted(sales["Category"].dropna().unique().tolist()),
            key=f"{prefix}_cat")
        sel["region"] = st.selectbox(
            "Region", ["All"] + sorted(sales["Region"].dropna().unique().tolist()),
            key=f"{prefix}_region")
        sel["dc"] = st.multiselect(
            "UNFI DC", sorted(sales["UNFI_DC"].dropna().unique().tolist()),
            key=f"{prefix}_dc")
        item_pool = sales if not sel["cat"] else sales[sales["Category"].isin(sel["cat"])]
        sel["item"] = st.selectbox(
            "Item", ["All"] + sorted(item_pool["Item Description"].dropna().unique().tolist()),
            key=f"{prefix}_item")
        sel["merch"] = st.selectbox(
            "Merchandiser", ["All", "Final Touch", "Basemakers", "Uncovered"],
            key=f"{prefix}_merch")
        sel["chan"] = st.selectbox("Channel", ["All", "In-Store", "Online"],
                                   key=f"{prefix}_chan")
        if show_comparison:
            st.markdown("---")
            sel["compare"] = st.radio("Compare vs", ["Prior Period", "Prior Year"],
                                      key=f"{prefix}_compare", horizontal=False)
    return sel

def apply_filters(df, sel, include_weeks=True):
    d = df
    if include_weeks:
        if sel["weeks"]:
            d = d[d["Week Ending"].isin(pd.to_datetime(sel["weeks"], format="%m/%d/%y"))]
        if sel["months"]:
            d = d[d["Month_Year"].isin(sel["months"])]
    if sel["cat"]:
        d = d[d["Category"].isin(sel["cat"])]
    if sel["region"] != "All":
        d = d[d["Region"] == sel["region"]]
    if sel["dc"]:
        d = d[d["UNFI_DC"].isin(sel["dc"])]
    if sel["item"] != "All":
        d = d[d["Item Description"] == sel["item"]]
    if sel["merch"] != "All":
        d = d[d["Merchandiser"] == sel["merch"]]
    if sel["chan"] != "All":
        d = d[d["Channel Type"] == sel["chan"]]
    return d

# ── HEADER ────────────────────────────────────────────────────────────────────
ALL_WEEKS = sorted(sales["Week Ending"].unique(), reverse=True)
latest_wk = pd.Timestamp(ALL_WEEKS[0]).strftime("%b %d, %Y")

st.markdown(f"""
<div class="vh-hdr">
  <div class="vh-hdr-left">
    <div>
      <div class="vh-hdr-title">VISTA HERMOSA</div>
      <div class="vh-hdr-sub">Whole Foods Market · Sales Intelligence · {OPEN_STORES} open stores</div>
    </div>
  </div>
  <div class="vh-hdr-badge">Latest week: {latest_wk}</div>
</div>""", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Performance Dashboard", "Broker Performance",
                            "Promo Comparisons"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PERFORMANCE DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    main1, panel1 = st.columns([4, 1.15], gap="medium")
    sel1 = render_filter_panel(panel1, "perf", show_comparison=True)
    compare_mode = sel1["compare"]

    with main1:
        filt = apply_filters(sales, sel1)                      # full filters (display)
        nfilt = apply_filters(sales, sel1, include_weeks=False)  # everything except weeks
        # Period windows always come from the full week list — never from the
        # week filter selection (fixes the broken L4 vs P4 comparison).
        cur4_wks  = ALL_WEEKS[:4]
        prev4_wks = ALL_WEEKS[4:8]
        cur4  = nfilt[nfilt["Week Ending"].isin(cur4_wks)]
        prev4 = nfilt[nfilt["Week Ending"].isin(prev4_wks)]

        cur4_units, cur4_sales_ = cur4["Unit Sales"].sum(), cur4["Net Sales"].sum()

        # Unit & net-sales cards: fixed Latest-4 vs Prior-4 (or PY same 4 wks)
        if compare_mode == "Prior Period":
            base_units, base_sales = prev4["Unit Sales"].sum(), prev4["Net Sales"].sum()
            cmp_lbl = "vs prior 4 wks"
        else:  # Prior Year — same 4 weeks, LY columns
            base_units, base_sales = cur4["Unit Sales LY"].sum(), cur4["Net Sales LY"].sum()
            cmp_lbl = "vs same 4 wks LY"

        delta_units = cur4_units - base_units
        delta_sales = cur4_sales_ - base_sales
        pct_units = (delta_units / base_units * 100) if base_units else 0
        pct_sales = (delta_sales / base_sales * 100) if base_sales else 0

        # Velocity cards: reflect the WEEK FILTER selection, averaged per
        # store / SKU / week (numerator and denominator both scale with the
        # number of selected weeks, so this stays a true per-week average).
        vsel = filt
        vsel_weeks = sorted(pd.to_datetime(vsel["Week Ending"].unique()))
        n_vsel = len(vsel_weeks)
        _wk = lambda n: f"{n} wk{'s' if n != 1 else ''}"
        def vcat(df, c): return df[df["Category"] == c]

        tort_vel  = velocity(vcat(vsel, "Tortillas"))
        tot_vel   = velocity(vcat(vsel, "Totopos"))
        tort_dvel = dollar_velocity(vcat(vsel, "Tortillas"))
        tot_dvel  = dollar_velocity(vcat(vsel, "Totopos"))

        if compare_mode == "Prior Period":
            # equal-length block of weeks immediately preceding the selection
            if vsel_weeks:
                earliest = min(vsel_weeks)
                prior_weeks = [w for w in ALL_WEEKS if w < earliest][:n_vsel]
            else:
                prior_weeks = []
            vprev = nfilt[nfilt["Week Ending"].isin(prior_weeks)]
            tort_vel_b  = velocity(vcat(vprev, "Tortillas"))
            tot_vel_b   = velocity(vcat(vprev, "Totopos"))
            tort_dvel_b = dollar_velocity(vcat(vprev, "Tortillas"))
            tot_dvel_b  = dollar_velocity(vcat(vprev, "Totopos"))
            vel_cmp_lbl = f"vs prior {_wk(n_vsel)}"
        else:  # Prior Year — same selected weeks, LY columns
            tort_vel_b  = velocity_ly(vcat(vsel, "Tortillas"))
            tot_vel_b   = velocity_ly(vcat(vsel, "Totopos"))
            tort_dvel_b = dollar_velocity_ly(vcat(vsel, "Tortillas"))
            tot_dvel_b  = dollar_velocity_ly(vcat(vsel, "Totopos"))
            vel_cmp_lbl = f"vs same {_wk(n_vsel)} LY"

        d_tort_u, d_tot_u = tort_vel - tort_vel_b, tot_vel - tot_vel_b
        d_tort_d, d_tot_d = tort_dvel - tort_dvel_b, tot_dvel - tot_dvel_b

        st.markdown(f'<div class="sec-hdr">Key Metrics · {compare_mode} comparison</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="kpi-row">', unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)

        with k1:
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-lbl">4-Week Unit Sales</div>
              <div class="kpi-val">{cur4_units:,.0f}</div>
              <div class="kpi-sub">units sold · latest 4 weeks</div>
              <div class="{delta_class(delta_units)}">{arrow(delta_units)} {abs(delta_units):,.0f} units ({abs(pct_units):.1f}%) {cmp_lbl}</div>
            </div>""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-lbl">4-Week Net Sales</div>
              <div class="kpi-val">${cur4_sales_:,.0f}</div>
              <div class="kpi-sub">net revenue · latest 4 weeks</div>
              <div class="{delta_class(delta_sales)}">{arrow(delta_sales)} ${abs(delta_sales):,.0f} ({abs(pct_sales):.1f}%) {cmp_lbl}</div>
            </div>""", unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-lbl">Avg Unit Velocity</div>
              <div style="display:flex;justify-content:center;gap:16px;margin:10px 0 4px">
                <div style="text-align:center">
                  <div style="font-size:11px;color:#888;font-weight:600">TORTILLAS</div>
                  <div class="kpi-val" style="font-size:28px">{tort_vel:.2f}</div>
                  <div class="{delta_class(d_tort_u)}" style="font-size:13px">{arrow(d_tort_u)} {abs(d_tort_u):.2f} {vel_cmp_lbl}</div>
                </div>
                <div style="width:1px;background:#E0E0E0;margin:0 2px"></div>
                <div style="text-align:center">
                  <div style="font-size:11px;color:#888;font-weight:600">TOTOPOS</div>
                  <div class="kpi-val" style="font-size:28px">{tot_vel:.2f}</div>
                  <div class="{delta_class(d_tot_u)}" style="font-size:13px">{arrow(d_tot_u)} {abs(d_tot_u):.2f} {vel_cmp_lbl}</div>
                </div>
              </div>
              <div class="kpi-sub">units / store / SKU / week · {_wk(n_vsel)} selected</div>
            </div>""", unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-lbl">Avg Dollar Velocity</div>
              <div style="display:flex;justify-content:center;gap:16px;margin:10px 0 4px">
                <div style="text-align:center">
                  <div style="font-size:11px;color:#888;font-weight:600">TORTILLAS</div>
                  <div class="kpi-val" style="font-size:28px">${tort_dvel:.2f}</div>
                  <div class="{delta_class(d_tort_d)}" style="font-size:13px">{arrow(d_tort_d)} ${abs(d_tort_d):.2f} {vel_cmp_lbl}</div>
                </div>
                <div style="width:1px;background:#E0E0E0;margin:0 2px"></div>
                <div style="text-align:center">
                  <div style="font-size:11px;color:#888;font-weight:600">TOTOPOS</div>
                  <div class="kpi-val" style="font-size:28px">${tot_dvel:.2f}</div>
                  <div class="{delta_class(d_tot_d)}" style="font-size:13px">{arrow(d_tot_d)} ${abs(d_tot_d):.2f} {vel_cmp_lbl}</div>
                </div>
              </div>
              <div class="kpi-sub">$ / store / SKU / week · {_wk(n_vsel)} selected</div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ── CHARTS — current vs comparison overlay ────────────────────────────
        st.markdown('<div class="sec-hdr">Trends Over Time</div>', unsafe_allow_html=True)

        chart_df = (filt.groupby("Week Ending")
                    .agg(Units=("Unit Sales", "sum"), Dollars=("Net Sales", "sum"),
                         Units_LY=("Unit Sales LY", "sum"), Dollars_LY=("Net Sales LY", "sum"))
                    .reset_index().sort_values("Week Ending"))

        def wk_velocity(g):
            sell = g[g["Unit Sales"] > 0]
            if sell.empty:
                return 0.0
            denom = sell.groupby(["Store Name", "Item Description"]).size().shape[0]
            return g["Unit Sales"].sum() / denom

        vel_df = (filt.groupby("Week Ending").apply(wk_velocity)
                  .reset_index(name="Velocity").sort_values("Week Ending"))

        c1, c2, c3 = st.columns(3)

        def bar_fig(df, x, y, title, color, prefix="", ly_col=None):
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df[x], y=df[y], name="This Year", marker_color=color,
                hovertemplate=f"<b>%{{x|%b %d}}</b><br>{prefix}%{{y:,.0f}}<extra></extra>"))
            if ly_col is not None and compare_mode == "Prior Year":
                fig.add_trace(go.Scatter(
                    x=df[x], y=df[ly_col], name="Prior Year", mode="lines+markers",
                    line=dict(color=C_RED, width=2, dash="dot"),
                    hovertemplate=f"<b>%{{x|%b %d}} LY</b><br>{prefix}%{{y:,.0f}}<extra></extra>"))
            fig.update_layout(
                title=dict(text=title, font=dict(size=15, color=C_DARK), x=0.5,
                           xanchor="center"),
                plot_bgcolor=C_WHITE, paper_bgcolor=C_WHITE,
                margin=dict(l=0, r=0, t=42, b=0), height=230,
                xaxis=dict(showgrid=False, tickformat="%b %d", tickangle=-35,
                           tickfont=dict(size=12)),
                yaxis=dict(showgrid=False,
                           tickformat=("$,.0f" if prefix == "$" else ",.0f"),
                           tickfont=dict(size=12)),
                bargap=0.25, showlegend=(ly_col is not None and compare_mode == "Prior Year"),
                legend=dict(orientation="h", y=1.15, x=0, font=dict(size=10)))
            return fig

        with c1:
            st.plotly_chart(bar_fig(chart_df, "Week Ending", "Units",
                                    "Units Sold by Week", C_YELLOW, ly_col="Units_LY"),
                            use_container_width=True, config={"displayModeBar": False})
        with c2:
            st.plotly_chart(bar_fig(chart_df, "Week Ending", "Dollars",
                                    "Net Sales ($) by Week", C_DARK, prefix="$",
                                    ly_col="Dollars_LY"),
                            use_container_width=True, config={"displayModeBar": False})
        with c3:
            st.plotly_chart(bar_fig(vel_df, "Week Ending", "Velocity",
                                    "Avg Unit Velocity by Week", C_GREEN),
                            use_container_width=True, config={"displayModeBar": False})

        # ── STORE PERFORMANCE ─────────────────────────────────────────────────
        st.markdown('<div class="sec-hdr">Store Performance</div>', unsafe_allow_html=True)

        pivot_raw = (filt.groupby(["Store Name", "Item Description", "Region",
                                   "Merchandiser", "UNFI_DC"])
                     .agg(Units=("Unit Sales", "sum"), Dollars=("Net Sales", "sum"),
                          Units_LY=("Unit Sales LY", "sum"), Dollars_LY=("Net Sales LY", "sum"))
                     .reset_index())

        sell_counts = (filt[filt["Unit Sales"] > 0]
                       .groupby(["Store Name", "Item Description", "Week Ending"])
                       .size().reset_index()
                       .groupby(["Store Name", "Item Description"])
                       .size().reset_index(name="Selling_Wks"))
        pivot_raw = pivot_raw.merge(sell_counts, on=["Store Name", "Item Description"],
                                    how="left")
        pivot_raw["Selling_Wks"] = pivot_raw["Selling_Wks"].fillna(0)
        pivot_raw["Avg Unit Vel."] = np.where(
            pivot_raw["Selling_Wks"] > 0,
            pivot_raw["Units"] / pivot_raw["Selling_Wks"], 0)
        pivot_raw["PY Units"] = pivot_raw["Units_LY"]
        pivot_raw["YoY %"] = np.where(pivot_raw["Units_LY"] > 0,
                                      (pivot_raw["Units"] / pivot_raw["Units_LY"] - 1) * 100,
                                      np.nan)

        pivot_raw = pivot_raw.merge(wks_since, on=["Store Name", "Item Description"],
                                    how="left")
        pivot_raw["Weeks Since Sale"] = pivot_raw["Weeks Since Sale"].fillna("OOS")
        pivot_raw["OOS"] = pivot_raw["Units"] == 0

        store_summary = (pivot_raw.groupby(["Store Name", "Region", "Merchandiser",
                                            "UNFI_DC"])
                         .agg(Units=("Units", "sum"), Dollars=("Dollars", "sum"),
                              Units_LY=("Units_LY", "sum"),
                              OOS_Count=("OOS", "sum"), Total_Items=("OOS", "count"))
                         .reset_index())
        store_summary["OOS Rate"] = (store_summary["OOS_Count"] /
                                     store_summary["Total_Items"] * 100).round(1)
        store_summary["YoY %"] = np.where(
            store_summary["Units_LY"] > 0,
            (store_summary["Units"] / store_summary["Units_LY"] - 1) * 100, np.nan)
        vel_lookup = pivot_raw.groupby("Store Name")["Avg Unit Vel."].mean()
        store_summary["Avg Unit Vel."] = store_summary["Store Name"].map(vel_lookup)

        tc1, tc2, tc3 = st.columns([3, 1, 1])
        with tc1:
            store_search = st.text_input("Search store", "", key="store_search",
                                         placeholder="Type to filter stores…")
        with tc2:
            oos_only = st.checkbox("Show OOS only", key="oos_only")
        with tc3:
            stale_only = st.checkbox("> 2 Wks Since Sale", key="stale_only")

        disp = store_summary.copy()
        if store_search:
            disp = disp[disp["Store Name"].str.contains(store_search, case=False, na=False)]
        if oos_only:
            disp = disp[disp["Store Name"].isin(
                pivot_raw[pivot_raw["OOS"]]["Store Name"].unique())]
        if stale_only:
            disp = disp[disp["Store Name"].isin(
                pivot_raw[pivot_raw["Weeks Since Sale"].apply(is_stale)]["Store Name"].unique())]
        disp = disp.sort_values("Dollars", ascending=False).reset_index(drop=True)

        oos_total = pivot_raw["OOS"].sum()
        if oos_total:
            st.markdown(f'<span class="oos-badge">{oos_total} store/item combos with 0 '
                        f'units in selected period</span>', unsafe_allow_html=True)

        show_items = st.checkbox("Expand to show item detail", key="show_items")

        def fmt_yoy(x):
            return f"{x:+.1f}%" if pd.notna(x) else "n/a"

        if show_items:
            store_tot = disp[["Store Name", "Region", "Merchandiser", "UNFI_DC",
                              "Units", "Units_LY", "YoY %", "Dollars",
                              "Avg Unit Vel.", "OOS Rate"]].copy()
            store_tot["Item"] = store_tot["Store Name"]
            store_tot["Row Type"] = "STORE"
            store_tot["Weeks Since Sale"] = ""
            store_tot["OOS"] = ""
            item_rows = []
            for store in disp["Store Name"]:
                items = pivot_raw[pivot_raw["Store Name"] == store]
                if oos_only:
                    items = items[items["OOS"]]
                if stale_only:
                    items = items[items["Weeks Since Sale"].apply(is_stale)]
                for _, ir in items.iterrows():
                    item_rows.append({
                        "Store Name": store, "Region": ir["Region"],
                        "Merchandiser": ir["Merchandiser"], "UNFI_DC": ir["UNFI_DC"],
                        "Item": "    " + ir["Item Description"],
                        "Units": ir["Units"], "Units_LY": ir["PY Units"],
                        "YoY %": ir["YoY %"], "Dollars": ir["Dollars"],
                        "Avg Unit Vel.": ir["Avg Unit Vel."], "OOS Rate": None,
                        "Weeks Since Sale": ir["Weeks Since Sale"],
                        "OOS": "Yes" if ir["OOS"] else "", "Row Type": "ITEM"})
            item_df = pd.DataFrame(item_rows) if item_rows else pd.DataFrame()
            combined = pd.concat([store_tot, item_df], ignore_index=True)
            combined["_sk"] = combined.apply(
                lambda r: r["Store Name"] + ("0" if r["Row Type"] == "STORE"
                                             else "1" + str(r["Item"])), axis=1)
            combined = combined.sort_values("_sk").drop("_sk", axis=1).reset_index(drop=True)
            combined["Net Sales ($)"] = combined["Dollars"].apply(
                lambda x: f"${x:,.0f}" if isinstance(x, (int, float)) else "")
            combined["Units"] = combined["Units"].apply(
                lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x)
            combined["PY Units"] = combined["Units_LY"].apply(
                lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else "")
            combined["YoY %"] = combined["YoY %"].apply(fmt_yoy)
            combined["Avg Unit Vel."] = combined["Avg Unit Vel."].apply(
                lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else "")
            combined["OOS Rate"] = combined["OOS Rate"].apply(
                lambda x: f"{x:.1f}%" if isinstance(x, (int, float)) else "")
            st.dataframe(
                combined[["Item", "Region", "UNFI_DC", "Merchandiser", "Units",
                          "PY Units", "YoY %", "Net Sales ($)", "Avg Unit Vel.",
                          "Weeks Since Sale", "OOS", "OOS Rate"]],
                use_container_width=True, height=520, hide_index=True,
                column_config={
                    "Item": st.column_config.TextColumn("Store / Item", width=240),
                    "UNFI_DC": st.column_config.TextColumn("UNFI DC", width=130),
                    "Avg Unit Vel.": st.column_config.TextColumn(
                        "Units/Store/SKU/Wk", width=130),
                    "Weeks Since Sale": st.column_config.TextColumn(
                        "Wks Since Sale", width=105)})
        else:
            sd = disp.copy()
            sd["Net Sales ($)"] = sd["Dollars"].apply(lambda x: f"${x:,.0f}")
            sd["Units"] = sd["Units"].apply(lambda x: f"{x:,.0f}")
            sd["PY Units"] = sd["Units_LY"].apply(lambda x: f"{x:,.0f}")
            sd["YoY %"] = sd["YoY %"].apply(fmt_yoy)
            sd["Avg Unit Vel."] = sd["Avg Unit Vel."].apply(lambda x: f"{x:.2f}")
            sd["OOS Rate"] = sd["OOS Rate"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(
                sd[["Store Name", "Region", "UNFI_DC", "Merchandiser", "Units",
                    "PY Units", "YoY %", "Net Sales ($)", "Avg Unit Vel.", "OOS Rate"]],
                use_container_width=True, height=480, hide_index=True,
                column_config={
                    "UNFI_DC": st.column_config.TextColumn("UNFI DC", width=130),
                    "Avg Unit Vel.": st.column_config.TextColumn(
                        "Units/Store/SKU/Wk", width=130)})

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — BROKER PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    main2, panel2 = st.columns([4, 1.15], gap="medium")
    sel2 = render_filter_panel(panel2, "brok", show_comparison=True)
    b_compare = sel2["compare"]

    with main2:
        st.markdown('<div class="sec-hdr">Broker Coverage Performance</div>',
                    unsafe_allow_html=True)
        bfilt = apply_filters(sales, sel2)
        bn = apply_filters(sales, sel2, include_weeks=False)
        cur4_wks, prev4_wks = ALL_WEEKS[:4], ALL_WEEKS[4:8]

        def broker_metrics(merch_label):
            s = bn[(bn["Merchandiser"] == merch_label) &
                   (bn["Week Ending"].isin(cur4_wks))]
            stores = s["Store Name"].nunique()
            units, dollars = s["Unit Sales"].sum(), s["Net Sales"].sum()
            vel_u, vel_d = velocity(s), dollar_velocity(s)
            if b_compare == "Prior Period":
                sp = bn[(bn["Merchandiser"] == merch_label) &
                        (bn["Week Ending"].isin(prev4_wks))]
                pvu, pvd = velocity(sp), dollar_velocity(sp)
            else:
                pvu, pvd = velocity_ly(s), dollar_velocity_ly(s)
            oos = s.groupby(["Store Name", "Item Description"])["Unit Sales"].sum()
            oos_pct = (oos == 0).mean() * 100 if len(oos) else 0
            return dict(stores=stores, units=units, dollars=dollars,
                        vel_u=vel_u, vel_d=vel_d, oos_pct=oos_pct,
                        du=vel_u - pvu, dd=vel_d - pvd)

        cmp_short = "vs P4" if b_compare == "Prior Period" else "vs LY"

        def broker_card(label, m, accent):
            du_cls = "broker-trend-pos" if m["du"] >= 0 else "broker-trend-neg"
            dd_cls = "broker-trend-pos" if m["dd"] >= 0 else "broker-trend-neg"
            du_arr = "▲" if m["du"] >= 0 else "▼"
            dd_arr = "▲" if m["dd"] >= 0 else "▼"
            oos_cls = ("oos-badge" if m["oos_pct"] > 15
                       else ("warn-badge" if m["oos_pct"] > 5 else "ok-badge"))
            return f"""
<div class="broker-card" style="border-top-color:{accent}">
  <div class="broker-name">{label}</div>
  <div class="broker-row"><span class="broker-key">Stores Covered</span>
    <span class="broker-val">{m['stores']:,}</span></div>
  <div class="broker-row"><span class="broker-key">4-Wk Units</span>
    <span class="broker-val">{m['units']:,.0f}</span></div>
  <div class="broker-row"><span class="broker-key">4-Wk Net Sales</span>
    <span class="broker-val">${m['dollars']:,.0f}</span></div>
  <div class="broker-row"><span class="broker-key">Units/Store/SKU/Wk</span>
    <span class="broker-val">{m['vel_u']:.2f}
      <span class="{du_cls}" style="font-size:11px">&nbsp;{du_arr}{abs(m['du']):.2f} {cmp_short}</span></span></div>
  <div class="broker-row"><span class="broker-key">$/Store/SKU/Wk</span>
    <span class="broker-val">${m['vel_d']:.2f}
      <span class="{dd_cls}" style="font-size:11px">&nbsp;{dd_arr}${abs(m['dd']):.2f} {cmp_short}</span></span></div>
  <div class="broker-row" style="border:none;padding-top:10px">
    <span class="broker-key">OOS Rate</span>
    <span class="{oos_cls}">{m['oos_pct']:.1f}% OOS</span></div>
</div>"""

        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            st.markdown(broker_card("Final Touch", broker_metrics("Final Touch"),
                                    C_YELLOW), unsafe_allow_html=True)
        with bc2:
            st.markdown(broker_card("Basemakers", broker_metrics("Basemakers"),
                                    C_GREEN), unsafe_allow_html=True)
        with bc3:
            st.markdown(broker_card("Uncovered / Direct", broker_metrics("Uncovered"),
                                    C_MGRAY), unsafe_allow_html=True)

        st.markdown('<div class="sec-hdr">Unit Velocity Trend by Merchandiser</div>',
                    unsafe_allow_html=True)
        trend_rows = []
        for merch in ["Final Touch", "Basemakers", "Uncovered"]:
            ms = bfilt[bfilt["Merchandiser"] == merch]
            for wk, grp in ms.groupby("Week Ending"):
                trend_rows.append({"Week Ending": wk, "Merchandiser": merch,
                                   "Velocity": velocity(grp)})
        trend_df = pd.DataFrame(trend_rows).sort_values("Week Ending") \
            if trend_rows else pd.DataFrame(columns=["Week Ending", "Merchandiser", "Velocity"])

        colors_map = {"Final Touch": C_YELLOW, "Basemakers": C_GREEN,
                      "Uncovered": C_MGRAY}
        fig_t = go.Figure()
        for merch in ["Final Touch", "Basemakers", "Uncovered"]:
            td = trend_df[trend_df["Merchandiser"] == merch]
            fig_t.add_trace(go.Bar(
                name=merch, x=td["Week Ending"], y=td["Velocity"],
                marker_color=colors_map[merch],
                hovertemplate="<b>%{x|%b %d}</b><br>Velocity: %{y:.2f}<extra></extra>"))
        fig_t.update_layout(
            barmode="group", plot_bgcolor=C_WHITE, paper_bgcolor=C_WHITE,
            margin=dict(l=0, r=0, t=10, b=0), height=260,
            xaxis=dict(showgrid=False, tickformat="%b %d", tickangle=-35,
                       tickfont=dict(size=12)),
            yaxis=dict(showgrid=False, tickfont=dict(size=12)),
            legend=dict(font=dict(size=11), orientation="h", yanchor="bottom",
                        y=1.02, xanchor="left", x=0),
            bargap=0.2, bargroupgap=0.05)
        st.plotly_chart(fig_t, use_container_width=True,
                        config={"displayModeBar": False})

        st.markdown('<div class="sec-hdr">Store-Level Broker Detail</div>',
                    unsafe_allow_html=True)
        bchk1, bchk2 = st.columns([1, 1])
        with bchk1:
            b_oos_only = st.checkbox("Show OOS only", key="b_oos_only")
        with bchk2:
            b_stale_only = st.checkbox("> 2 Wks Since Sale", key="b_stale_only")

        broker_item = (bfilt.groupby(["Store Name", "Item Description", "Region",
                                      "Merchandiser", "UNFI_DC"])
                       .agg(Units=("Unit Sales", "sum"), Dollars=("Net Sales", "sum"),
                            Units_LY=("Unit Sales LY", "sum"))
                       .reset_index())
        broker_item["OOS"] = broker_item["Units"] == 0
        broker_item["YoY %"] = np.where(
            broker_item["Units_LY"] > 0,
            (broker_item["Units"] / broker_item["Units_LY"] - 1) * 100, np.nan)
        broker_item = broker_item.merge(wks_since,
                                        on=["Store Name", "Item Description"], how="left")
        broker_item["Weeks Since Sale"] = broker_item["Weeks Since Sale"].fillna("OOS")
        if b_oos_only:
            broker_item = broker_item[broker_item["OOS"]]
        if b_stale_only:
            broker_item = broker_item[broker_item["Weeks Since Sale"].apply(is_stale)]
        broker_item = broker_item.sort_values(
            ["Store Name", "Item Description"]).reset_index(drop=True)
        broker_item["Net Sales ($)"] = broker_item["Dollars"].apply(lambda x: f"${x:,.0f}")
        broker_item["Units"] = broker_item["Units"].apply(lambda x: f"{x:,.0f}")
        broker_item["PY Units"] = broker_item["Units_LY"].apply(lambda x: f"{x:,.0f}")
        broker_item["YoY %"] = broker_item["YoY %"].apply(
            lambda x: f"{x:+.1f}%" if pd.notna(x) else "n/a")
        broker_item["OOS"] = broker_item["OOS"].apply(lambda x: "Yes" if x else "")
        st.dataframe(
            broker_item[["Store Name", "Item Description", "Region", "UNFI_DC",
                         "Merchandiser", "Units", "PY Units", "YoY %",
                         "Net Sales ($)", "Weeks Since Sale", "OOS"]],
            use_container_width=True, height=420, hide_index=True,
            column_config={
                "Item Description": st.column_config.TextColumn("Item", width=190),
                "UNFI_DC": st.column_config.TextColumn("UNFI DC", width=125),
                "Weeks Since Sale": st.column_config.TextColumn("Wks Since Sale",
                                                                width=105)})

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — PROMO COMPARISONS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    main3, panel3 = st.columns([4, 1.15], gap="medium")

    with panel3:
        st.markdown('<div class="filter-title">FILTERS — THIS PAGE</div>',
                    unsafe_allow_html=True)
        p_region = st.selectbox(
            "Region", ["All"] + sorted(sales["Region"].dropna().unique().tolist()),
            key="promo_region")
        p_dc = st.multiselect(
            "UNFI DC", sorted(sales["UNFI_DC"].dropna().unique().tolist()),
            key="promo_dc")
        p_chan = st.selectbox("Channel", ["All", "In-Store", "Online"], key="promo_chan")
        st.markdown("---")
        st.caption("Promo periods come from the shared **VH x WFM Promo Calendar** "
                   "Google Sheet. Only Confirmed / Live / Completed promos appear.")

    with main3:
        st.markdown('<div class="sec-hdr">Promo Comparisons</div>',
                    unsafe_allow_html=True)

        if promo_cal.empty:
            st.warning("No promo periods found. Add promos to the VH x WFM Promo "
                       "Calendar Google Sheet (Status = Confirmed/Live/Completed), "
                       "or place a dim_promo_periods.csv next to the app. "
                       "The sheet must be link-viewable for the app to read it.")
        else:
            # Build promo period registry
            periods = (promo_cal.groupby("Promo_Name")
                       .agg(Start=("Start_Date", "min"), End=("End_Date", "max"))
                       .reset_index().sort_values("Start", ascending=False))
            period_names = periods["Promo_Name"].tolist()

            p_sales = sales.copy()
            if p_region != "All":
                p_sales = p_sales[p_sales["Region"] == p_region]
            if p_dc:
                p_sales = p_sales[p_sales["UNFI_DC"].isin(p_dc)]
            if p_chan != "All":
                p_sales = p_sales[p_sales["Channel Type"] == p_chan]

            def promo_slice(name):
                row = periods[periods["Promo_Name"] == name].iloc[0]
                upcs = set(promo_cal[promo_cal["Promo_Name"] == name]["UPC"].dropna())
                d = p_sales[(p_sales["Week Ending"] >= row["Start"]) &
                            (p_sales["Week Ending"] <= row["End"] + pd.Timedelta(days=6))]
                if upcs:
                    d = d[d["Scan Code"].isin(upcs)]
                n_wks = max(d["Week Ending"].nunique(), 1)
                return d, row["Start"], row["End"], n_wks

            def baseline_slice(name, upcs_of):
                """4 weeks immediately before the promo start, same items."""
                row = periods[periods["Promo_Name"] == name].iloc[0]
                pre_end = row["Start"] - pd.Timedelta(days=1)
                pre_start = pre_end - pd.Timedelta(weeks=4)
                d = p_sales[(p_sales["Week Ending"] > pre_start) &
                            (p_sales["Week Ending"] <= pre_end)]
                if upcs_of:
                    d = d[d["Scan Code"].isin(upcs_of)]
                n_wks = max(d["Week Ending"].nunique(), 1)
                return d, n_wks

            # ── Promo A / Promo B cards, each with its own period dropdown ─────
            ca, cb = st.columns(2)

            def promo_card(container, key, default_idx):
                with container:
                    name = st.selectbox("Promotional period", period_names,
                                        index=min(default_idx, len(period_names) - 1),
                                        key=key)
                    d, s, e, n_wks = promo_slice(name)
                    units, dollars = d["Unit Sales"].sum(), d["Net Sales"].sum()
                    vel = velocity(d)
                    st.markdown(f"""
                    <div class="kpi-card">
                      <div class="kpi-lbl">{name}</div>
                      <div class="kpi-sub">{s:%b %d} – {e:%b %d, %Y} · {n_wks} wks in data</div>
                      <div style="display:flex;gap:26px;margin-top:12px">
                        <div><div class="kpi-sub">UNITS</div>
                             <div class="kpi-val" style="font-size:26px">{units:,.0f}</div></div>
                        <div><div class="kpi-sub">NET SALES</div>
                             <div class="kpi-val" style="font-size:26px">${dollars:,.0f}</div></div>
                        <div><div class="kpi-sub">U/STORE/SKU/WK</div>
                             <div class="kpi-val" style="font-size:26px">{vel:.2f}</div></div>
                      </div>
                    </div>""", unsafe_allow_html=True)
                    return name, d, n_wks

            name_a, da, wks_a = promo_card(ca, "promo_a", 0)
            name_b, db, wks_b = promo_card(cb, "promo_b",
                                           1 if len(period_names) > 1 else 0)

            # ── Promo vs Promo — item-level growth table ───────────────────────
            st.markdown(f'<div class="sec-hdr">Promo vs Promo by Item — '
                        f'{name_a} vs {name_b}</div>', unsafe_allow_html=True)

            def item_agg(d, n_wks, suffix):
                g = (d.groupby("Item Description")
                     .agg(**{f"Units {suffix}": ("Unit Sales", "sum"),
                             f"$ {suffix}": ("Net Sales", "sum")})
                     .reset_index())
                vels = {}
                for item, grp in d.groupby("Item Description"):
                    vels[item] = velocity(grp)
                g[f"Vel {suffix}"] = g["Item Description"].map(vels)
                g[f"Units/Wk {suffix}"] = g[f"Units {suffix}"] / n_wks
                return g

            ia = item_agg(da, wks_a, "A")
            ib = item_agg(db, wks_b, "B")
            comp = ia.merge(ib, on="Item Description", how="outer").fillna(0)
            comp["Unit Growth"] = comp["Units A"] - comp["Units B"]
            comp["Unit Growth %"] = np.where(
                comp["Units B"] > 0,
                (comp["Units A"] / comp["Units B"] - 1) * 100, np.nan)
            comp["$ Growth"] = comp["$ A"] - comp["$ B"]
            comp["$ Growth %"] = np.where(
                comp["$ B"] > 0, (comp["$ A"] / comp["$ B"] - 1) * 100, np.nan)
            comp = comp.sort_values("$ A", ascending=False)

            show = comp.copy()
            for c in ["Units A", "Units B", "Unit Growth"]:
                show[c] = show[c].apply(lambda x: f"{x:,.0f}")
            for c in ["$ A", "$ B", "$ Growth"]:
                show[c] = show[c].apply(lambda x: f"${x:,.0f}")
            for c in ["Vel A", "Vel B"]:
                show[c] = show[c].apply(lambda x: f"{x:.2f}")
            for c in ["Unit Growth %", "$ Growth %"]:
                show[c] = show[c].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "n/a")
            st.caption(f"A = {name_a} ({wks_a} wks) · B = {name_b} ({wks_b} wks). "
                       "Growth = A vs B. Vel = units/store/SKU/wk (length-neutral).")
            st.dataframe(
                show[["Item Description", "Units A", "Units B", "Unit Growth",
                      "Unit Growth %", "$ A", "$ B", "$ Growth", "$ Growth %",
                      "Vel A", "Vel B"]],
                use_container_width=True, hide_index=True,
                column_config={"Item Description":
                               st.column_config.TextColumn("Item", width=210)})

            # ── Promo lift vs pre-promo baseline ───────────────────────────────
            st.markdown('<div class="sec-hdr">Promo Lift vs 4-Week Pre-Promo '
                        'Baseline</div>', unsafe_allow_html=True)
            lift_name = st.selectbox("Promotional period", period_names,
                                     key="promo_lift")
            dl, sL, eL, wksL = promo_slice(lift_name)
            upcs_l = set(promo_cal[promo_cal["Promo_Name"] == lift_name]["UPC"].dropna())
            dbase, wks_base = baseline_slice(lift_name, upcs_l)

            lift_rows = []
            items_all = sorted(set(dl["Item Description"]) | set(dbase["Item Description"]))
            for item in items_all:
                pi = dl[dl["Item Description"] == item]
                bi = dbase[dbase["Item Description"] == item]
                pv, bv = velocity(pi), velocity(bi)
                pu_wk = pi["Unit Sales"].sum() / wksL
                bu_wk = bi["Unit Sales"].sum() / wks_base if len(bi) else 0
                lift_rows.append({
                    "Item": item,
                    "Baseline Units/Wk": bu_wk, "Promo Units/Wk": pu_wk,
                    "Baseline Vel": bv, "Promo Vel": pv,
                    "Vel Lift %": (pv / bv - 1) * 100 if bv else np.nan,
                    "Units/Wk Lift %": (pu_wk / bu_wk - 1) * 100 if bu_wk else np.nan})
            lift_df = pd.DataFrame(lift_rows)
            if not lift_df.empty:
                ls = lift_df.copy()
                for c in ["Baseline Units/Wk", "Promo Units/Wk"]:
                    ls[c] = ls[c].apply(lambda x: f"{x:,.0f}")
                for c in ["Baseline Vel", "Promo Vel"]:
                    ls[c] = ls[c].apply(lambda x: f"{x:.2f}")
                for c in ["Vel Lift %", "Units/Wk Lift %"]:
                    ls[c] = ls[c].apply(
                        lambda x: f"{x:+.1f}%" if pd.notna(x) else "n/a")
                st.caption(f"{lift_name}: {sL:%b %d} – {eL:%b %d, %Y} vs the 4 weeks "
                           "immediately prior. Vel = units/store/SKU/wk.")
                st.dataframe(ls, use_container_width=True, hide_index=True,
                             column_config={"Item":
                                            st.column_config.TextColumn(width=210)})
            else:
                st.info("No sales rows found in this promo window for the selected filters.")
