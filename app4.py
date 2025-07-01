import streamlit as st
import pandas as pd
import random
from itertools import product, combinations

st.set_page_config(page_title="EPP 1 Revenue Forecast Simulator", layout="wide")
st.title("EPP 1 Revenue Forecast Simulator")

# -------------------------
# USER INPUTS
# -------------------------
st.sidebar.header("Simulation Settings")

months = st.sidebar.slider("Number of Months (Forecast Period)", 1, 12, 6)
net_target = st.sidebar.number_input("Net Profit Target", value=1_000_000)
coaching_price = st.sidebar.number_input("Coaching Price per Engagement", value=8750)
min_coaching = st.sidebar.number_input("Minimum Coaching Clients", value=0)
max_coaching = st.sidebar.number_input("Maximum Coaching Clients", value=20)

# Deal simulation settings
st.sidebar.subheader("Deal Simulation Settings")
total_deal_simulations = st.sidebar.number_input("Total Number of Deal Plans to Simulate", value=500000, step=100000)

# Deal Ranges
min_deals = st.sidebar.number_input("Min Deals per Month", value=0)
max_deals = st.sidebar.number_input("Max Deals per Month", value=3)
deal_range = list(range(min_deals, max_deals + 1))

# Deal Values and Commission Rates
st.sidebar.subheader("Deal Values")
deal_values = st.sidebar.multiselect(
    "Select Deal Values",
    [500_000, 1_000_000, 1_500_000, 2_000_000, 2_500_000],
    default=[500_000, 1_500_000, 2_500_000]
)

st.sidebar.subheader("Commission Rates")
commission_rates = st.sidebar.multiselect(
    "Select Commission Rates",
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
        {"label": "Insurance (Liability, E&O, Cyber)", "amount": 300.0},
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
# SIMULATION
# -------------------------
if st.button("Run Simulation"):
    st.markdown("### Results")
    results = []

    with st.spinner("Running simulation..."):
        monthly_deal_options = [(v, r) for v in deal_values for r in commission_rates]

        for total_coaching in range(min_coaching, max_coaching + 1):
            coaching_revenue = total_coaching * coaching_price

            for _ in range(int(total_deal_simulations)):
                deal_plan = []
                monthly_commissions = [0] * months

                for m in range(months):
                    deals_this_month = random.choice(deal_range)
                    selected_deals = random.sample(monthly_deal_options, k=min(deals_this_month, len(monthly_deal_options)))

                    for deal_value, rate in selected_deals:
                        commission = deal_value * rate
                        monthly_payment = commission / 12

                        for j in range(m + 2, m + 14):
                            if j >= months:
                                break
                            monthly_commissions[j] += monthly_payment

                    for deal_value, rate in selected_deals:
                        deal_plan.append((m+1, deal_value, rate))

                commission_revenue = sum(monthly_commissions)
                total_revenue = coaching_revenue + commission_revenue
                total_expense = total_expense_per_month * months
                net_profit = total_revenue - total_expense

                if net_profit >= net_target or net_profit >= 800000:
                    results.append({
                        "Total Coaching Clients": total_coaching,
                        "Deal Plan": ",".join([f"{m},{v},{r}" for m, v, r in deal_plan]),
                        "Total Coaching Revenue": coaching_revenue,
                        "Deal Revenue (2025 Recognized)": commission_revenue,
                        "Total Revenue": total_revenue,
                        "Total Expenses": total_expense,
                        "Net Profit": round(net_profit, 2),
                        "Workload Score": total_coaching + len(deal_plan)
                    })

    if results:
        df = pd.DataFrame(results)
        st.success(f"Found {len(df)} matching results (≥ $800K net profit)")
        df = df.sort_values(by=["Net Profit", "Workload Score"], ascending=[False, True]).reset_index(drop=True)
        st.dataframe(df.head(100))

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Results as CSV", data=csv, file_name="forecast_results.csv", mime="text/csv")
    else:
        st.warning("No combinations reached the profit threshold. Try adjusting your parameters.")
