import streamlit as st
import pandas as pd
import itertools
import random
import time

st.set_page_config(page_title="EPP 1 Revenue Forecast Simulator", layout="wide")
st.title("EPP 1 Revenue Forecast Simulator")

# -------------------------
# USER INPUTS
# -------------------------
st.sidebar.header("Simulation Settings")

months = st.sidebar.slider("Number of Months (Forecast Period)", 1, 12, 6)
net_target = st.sidebar.number_input("Net Profit Target ($)", value=1_000_000)
near_target = st.sidebar.number_input("Near-Qualified Threshold ($)", value=800_000)
coaching_price = st.sidebar.number_input("Coaching Price per Engagement", value=8750)

total_simulations = st.sidebar.number_input("Total Number of Deal Plans to Simulate", value=100000, step=10000)
batch_size = st.sidebar.number_input("Batch Size per Simulation Loop", value=1000, step=500)

min_deals = st.sidebar.number_input("Min Deals per Month", value=0)
max_deals = st.sidebar.number_input("Max Deals per Month", value=3)
deal_range = range(min_deals, max_deals + 1)

min_coaching = st.sidebar.number_input("Min Coaching Clients per Month", value=0)
max_coaching = st.sidebar.number_input("Max Coaching Clients per Month", value=3)
coaching_range = range(min_coaching, max_coaching + 1)

deal_values = st.sidebar.multiselect(
    "Deal Values",
    [500_000, 1_000_000, 1_500_000, 2_000_000, 2_500_000],
    default=[500_000, 1_500_000, 2_500_000]
)

commission_rates = st.sidebar.multiselect(
    "Commission Rates",
    [0.05, 0.07, 0.11, 0.13, 0.17],
    default=[0.05, 0.11, 0.17]
)

# -------------------------
# EXPENSES (Main Body)
# -------------------------
st.markdown("## Monthly Expenses")

if "expenses" not in st.session_state:
    st.session_state.expenses = [
        {"label": "Travel & Expenses", "amount": 6000.0},
        {"label": "Marketing Costs", "amount": 600.0},
        {"label": "Marketing Agency", "amount": 3000.0},
        {"label": "Full-Time VA Salary", "amount": 1200.0},
        {"label": "Part-Time VA Salary", "amount": 400.0},
        {"label": "Finance VA Salary", "amount": 400.0},
        {"label": "AI/Automations", "amount": 250.0},
        {"label": "Software & SaaS Tools", "amount": 600.0},
        {"label": "Legal & Compliance Fees", "amount": 300.0},
        {"label": "Insurance (Liability, E&O, Cyber)", "amount": 300.0}
    ]

for i, exp in enumerate(st.session_state.expenses):
    col1, col2, col3 = st.columns([4, 3, 1])
    exp["label"] = col1.text_input(f"Label {i+1}", value=exp["label"], key=f"label_{i}")
    exp["amount"] = col2.number_input(f"Amount {i+1}", value=float(exp["amount"]), min_value=0.0, key=f"amount_{i}")
    if col3.button("❌", key=f"remove_{i}"):
        st.session_state.expenses.pop(i)
        st.rerun()

if st.button("Add Another Expense"):
    st.session_state.expenses.append({"label": f"Expense {len(st.session_state.expenses)+1}", "amount": 0.0})
    st.rerun()

total_expense_per_month = sum(exp["amount"] for exp in st.session_state.expenses)
st.markdown(f"**Total Monthly Expense:** ${total_expense_per_month:,.2f}")

# -------------------------
# SIMULATION ENGINE
# -------------------------
if st.button("Run Simulation"):
    st.markdown("## 🔍 Simulating... Please wait.")
    coaching_options = list(range(min_coaching, max_coaching + 1))
    qualified = []
    near_qualified = []

    monthly_deal_variants = list(itertools.product(deal_values, commission_rates))

    progress = st.progress(0, text="Starting...")

    for sim in range(0, total_simulations, batch_size):
        for _ in range(batch_size):
            coaching_total = sum(random.choices(coaching_options, k=months))
            coaching_revenue = coaching_total * coaching_price

            monthly_commission_2025 = [0] * months

            for month in range(months):
                deals = []
                deal_count = random.randint(min_deals, max_deals)
                possible_deals = random.sample(monthly_deal_variants, min(deal_count, len(monthly_deal_variants)))
                for dv, cr in possible_deals:
                    deals.append((dv, cr))

                for deal_value, commission_rate in deals:
                    commission = deal_value * commission_rate
                    spread = commission / 12
                    for j in range(month + 2, month + 14):
                        if j < months:
                            monthly_commission_2025[j] += spread

            commission_revenue = sum(monthly_commission_2025)
            total_revenue = commission_revenue + coaching_revenue
            total_expense = total_expense_per_month * months
            net_profit = total_revenue - total_expense

            result = {
                "Total Coaching Clients": coaching_total,
                "Total Coaching Revenue": coaching_revenue,
                "Total Deal Revenue (Recognized)": commission_revenue,
                "Total Revenue": round(total_revenue, 2),
                "Total Expense": round(total_expense, 2),
                "Net Profit": round(net_profit, 2)
            }

            if net_profit >= net_target:
                qualified.append(result)
            elif net_profit >= near_target:
                near_qualified.append(result)

        progress.progress(min((sim + batch_size) / total_simulations, 1.0), text=f"Simulating... {sim + batch_size} / {total_simulations}")

    # -------------------------
    # RESULTS
    # -------------------------
    st.markdown("## ✅ Simulation Complete")

    if qualified:
        st.success(f"🎯 {len(qualified)} Qualified Scenarios (≥ ${net_target:,})")
        df_qualified = pd.DataFrame(qualified).sort_values(by="Net Profit", ascending=False)
        st.dataframe(df_qualified.head(100))
        st.download_button("Download Qualified Results", df_qualified.to_csv(index=False), "qualified_results.csv", "text/csv")
    else:
        st.warning("No qualified combinations met the $1M net profit goal.")

    if near_qualified:
        st.info(f"🟡 {len(near_qualified)} Near-Qualified Scenarios (≥ ${near_target:,})")
        df_near = pd.DataFrame(near_qualified).sort_values(by="Net Profit", ascending=False)
        st.dataframe(df_near.head(100))
        st.download_button("Download Near-Qualified Results", df_near.to_csv(index=False), "near_qualified_results.csv", "text/csv")
    else:
        st.warning("No near-qualified combinations (≥ $800K net profit) were found.")
