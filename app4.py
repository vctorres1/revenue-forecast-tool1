import streamlit as st
import pandas as pd
import itertools

st.set_page_config(page_title="EPP 1 Revenue Forecaster", layout="wide")
st.title("Greedy Revenue Forecast Simulator")

# -------------------------
# USER INPUTS
# -------------------------
st.sidebar.header("Simulation Settings")

months = st.sidebar.slider("Forecast Months", 1, 12, 6)
net_target = st.sidebar.number_input("Net Profit Target ($)", value=1_000_000)
coaching_price = st.sidebar.number_input("Coaching Price ($ per client)", value=8750)

# Deal inputs
deal_values = st.sidebar.multiselect("Deal Values", [500_000, 1_000_000, 1_500_000, 2_000_000, 2_500_000], default=[500_000, 1_500_000, 2_500_000])
commission_rates = st.sidebar.multiselect("Commission Rates", [0.05, 0.07, 0.11, 0.13, 0.17], default=[0.05, 0.11, 0.17])
max_deals_per_month = st.sidebar.number_input("Max Total Deals per Month", min_value=1, max_value=10, value=3)

# Expenses
total_expense_per_month = st.sidebar.number_input("Total Monthly Expense ($)", value=8859.0, step=100.0)

# -------------------------
# SIMULATION ENGINE
# -------------------------
def simulate_greedy():
    deal_options = [(v, r) for v in deal_values for r in commission_rates]
    all_monthly_plans = []
    monthly_commission = [0] * months

    for m in range(months):
        month_plan = []
        month_total = 0

        for _ in range(max_deals_per_month):
            best_deal = None
            best_value = 0
            for deal_value, rate in deal_options:
                commission = deal_value * rate / 12
                if month_total + commission <= net_target:
                    if commission > best_value:
                        best_value = commission
                        best_deal = (deal_value, rate)

            if best_deal:
                month_plan.append(best_deal)
                month_total += best_value

        all_monthly_plans.append(month_plan)

        for value, rate in month_plan:
            commission = value * rate / 12
            for j in range(m + 2, m + 14):
                if j < months:
                    monthly_commission[j] += commission

    total_commission = sum(monthly_commission)
    revenue_gap = net_target + (total_expense_per_month * months) - total_commission
    coaching_needed = max(0, int(revenue_gap // coaching_price))
    coaching_revenue = coaching_needed * coaching_price
    total_revenue = total_commission + coaching_revenue
    net_profit = total_revenue - total_expense_per_month * months

    return {
        "Monthly Deal Plans": all_monthly_plans,
        "Monthly Recognized Commission": monthly_commission,
        "Total Coaching Clients": coaching_needed,
        "Total Commission Revenue": round(total_commission, 2),
        "Coaching Revenue": round(coaching_revenue, 2),
        "Total Revenue": round(total_revenue, 2),
        "Net Profit": round(net_profit, 2),
    }

# -------------------------
# RUN SIMULATION
# -------------------------
if st.button("Run Simulation"):
    with st.spinner("Simulating optimal revenue plan..."):
        result = simulate_greedy()

        st.subheader("📅 Monthly Deal Breakdown")
        for idx, month in enumerate(result["Monthly Deal Plans"]):
            st.markdown(f"**Month {idx + 1}**: " + ", ".join([f"${v:,}@{int(r*100)}%" for v, r in month]) or "No deals")

        st.subheader("📊 Results")
        st.markdown(f"**Total Recognized Commission:** ${result['Total Commission Revenue']:,}")
        st.markdown(f"**Coaching Clients Needed:** {result['Total Coaching Clients']} → Revenue = ${result['Coaching Revenue']:,}")
        st.markdown(f"**Total Revenue:** ${result['Total Revenue']:,}")
        st.markdown(f"**Net Profit:** ${result['Net Profit']:,}")

        if result['Net Profit'] >= net_target:
            st.success("✅ Success! Net profit target achieved.")
        else:
            st.warning("⚠️ Net profit target not met. Consider adjusting parameters.")
