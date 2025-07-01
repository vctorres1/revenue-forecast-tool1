import streamlit as st
import pandas as pd
import itertools
import random

st.set_page_config(page_title="EPP 1 Revenue Forecast Simulator", layout="wide")
st.title("EPP 1 Revenue Forecast Simulator")

# -------------------------
# USER INPUTS
# -------------------------
st.sidebar.header("Simulation Settings")

months = st.sidebar.slider("Number of Months (Forecast Period)", 1, 12, 6)
net_target = st.sidebar.number_input("Net Profit Target", value=1_000_000)
coaching_price = st.sidebar.number_input("Coaching Price per Engagement", value=8750)
num_mixed_deal_plans = st.sidebar.number_input("Number of Deal Plans to Simulate", value=10000, step=1000)
num_coaching_plans = st.sidebar.number_input("Number of Coaching Plans to Simulate", value=500, step=100)

# Deal Ranges
min_deals = st.sidebar.number_input("Min Deals per Month", value=0)
max_deals = st.sidebar.number_input("Max Deals per Month", value=3)
deal_range = range(min_deals, max_deals + 1)

# Coaching Ranges
min_coaching = st.sidebar.number_input("Min Coaching Clients per Month", value=0)
max_coaching = st.sidebar.number_input("Max Coaching Clients per Month", value=3)
coaching_range = list(range(min_coaching, max_coaching + 1))

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
# EXPENSES
# -------------------------
st.markdown("## Monthly Expenses")

if "expenses" not in st.session_state:
    st.session_state.expenses = [
        {"label": "Travel & Expenses", "amount": 0.0},
        {"label": "Marketing Costs", "amount": 0.0},
        {"label": "Marketing Agency", "amount": 0.0},
        {"label": "AI/Automations", "amount": 0.0},
        {"label": "Software & SaaS Tools", "amount": 0.0},
        {"label": "Legal & Compliance Fees", "amount": 0.0},
        {"label": "Insurance (Liability, E&O, Cyber)", "amount": 0.0},
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
# RUN SIMULATION
# -------------------------
if st.button("Run Simulation"):
    coaching_plans = [tuple(random.choices(coaching_range, k=months)) for _ in range(num_coaching_plans)]

    # Generate randomized per-month deal recommendations
    monthly_deal_plans = []
    for _ in range(int(num_mixed_deal_plans)):
        monthly_plan = []
        for _ in range(months):
            month_deals = [
                (1, random.choice(deal_values), random.choice(commission_rates))
                for _ in range(random.randint(min_deals, max_deals))
            ]
            monthly_plan.append(month_deals)
        monthly_deal_plans.append(monthly_plan)

    results = []
    progress_text = "🔄 Running simulation... please wait"
    progress_bar = st.progress(0, text=progress_text)

    for idx, c_plan in enumerate(coaching_plans):
        coaching_revenue = sum(c * coaching_price for c in c_plan)

        for d_plan in monthly_deal_plans:
            monthly_commission_2025 = [0] * months

            for i, month_deals in enumerate(d_plan):
                for deal_count, deal_value, commission_rate in month_deals:
                    commission_per_deal = deal_value * commission_rate
                    total_commission = deal_count * commission_per_deal
                    monthly_payment = total_commission / 12
                    for j in range(i + 2, i + 14):
                        if j >= months:
                            break
                        monthly_commission_2025[j] += monthly_payment

            commission_revenue = sum(monthly_commission_2025)
            total_revenue = coaching_revenue + commission_revenue
            total_expenses = total_expense_per_month * months
            net_profit = total_revenue - total_expenses

            if net_profit >= net_target:
                results.append({
                    "Total Coaching Revenue": coaching_revenue,
                    "Total Deal Revenue (Recognized 2025)": commission_revenue,
                    "Total Revenue": round(total_revenue, 2),
                    "Net Profit": round(net_profit, 2),
                    "Total Coaching": sum(c_plan),
                    "Total Deals": sum(len(month) for month in d_plan),
                    "Deal Plan": ",".join([f"{x[0]},{x[1]},{x[2]}" for month in d_plan for x in month]),
                })

        if idx % 10 == 0 or idx == len(coaching_plans) - 1:
            progress_bar.progress((idx + 1) / len(coaching_plans), text=progress_text)

    # -------------------------
    # OUTPUT
    # -------------------------
    if results:
        st.success(f"✅ Found {len(results)} profitable scenario(s) meeting or exceeding ${net_target:,} target")
        df = pd.DataFrame(results)
        df = df.sort_values(by=["Net Profit"], ascending=False).reset_index(drop=True)
        st.dataframe(df.head(100))

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Results as CSV", data=csv, file_name="forecast_results.csv", mime="text/csv")
    else:
        st.warning("⚠️ No combinations reached the net profit target. Try adjusting your parameters.")
