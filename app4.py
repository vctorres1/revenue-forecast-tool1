import streamlit as st
import pandas as pd
import random
import time

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(page_title="Revenue Forecast Simulator", layout="wide")
st.title("💼 EPP 1 Revenue Forecast Simulator")

# -------------------------
# SIDEBAR CONFIGURATION
# -------------------------
st.sidebar.header("🛠️ Simulation Settings")
months = st.sidebar.slider("Number of Months", 1, 12, 6)
net_target = st.sidebar.number_input("Net Profit Target", value=1_000_000)
coaching_price = st.sidebar.number_input("Coaching Price per Engagement", value=8750)

batch_size = st.sidebar.number_input("Batch Size (per iteration)", value=5000, step=1000)
total_deal_plans = st.sidebar.number_input("Total Number of Deal Plans to Simulate", value=100000, step=10000)

min_deals = st.sidebar.number_input("Min Deals per Month", value=0)
max_deals = st.sidebar.number_input("Max Deals per Month", value=3)
deal_count_range = list(range(min_deals, max_deals + 1))

st.sidebar.subheader("Deal Values")
deal_values = st.sidebar.multiselect("Select Deal Values", [500_000, 1_000_000, 1_500_000, 2_000_000, 2_500_000], default=[500_000, 1_500_000, 2_500_000])

st.sidebar.subheader("Commission Rates")
commission_rates = st.sidebar.multiselect("Select Commission Rates", [0.05, 0.07, 0.11, 0.13, 0.17], default=[0.05, 0.11, 0.17])

# -------------------------
# EXPENSES
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

total_monthly_expense = sum(exp["amount"] for exp in st.session_state.expenses)
st.markdown(f"**Total Monthly Expense:** ${total_monthly_expense:,.2f}")

# -------------------------
# SIMULATION ENGINE
# -------------------------
if st.button("🚀 Run Simulation"):
    start_time = time.time()
    results = []
    runs = int(total_deal_plans // batch_size)
    deal_types = [(val, rate) for val in deal_values for rate in commission_rates]

    progress_bar = st.progress(0)
    status_placeholder = st.empty()

    for batch in range(runs):
        for _ in range(batch_size):
            deal_plan = []
            commission_schedule = [0.0] * months

            for month in range(months):
                deals_this_month = []
                for _ in range(random.choice(deal_count_range)):
                    val, rate = random.choice(deal_types)
                    deals_this_month.append((val, rate))

                    # Revenue recognition starts 2 months after closing, spread over 12 months
                    commission = val * rate
                    monthly_payment = commission / 12
                    for offset in range(2, 14):
                        future_month = month + offset
                        if future_month < months:
                            commission_schedule[future_month] += monthly_payment

                deal_plan.append(deals_this_month)

            # Vary number of coaching clients
            coaching_clients_total = random.randint(0, months * 3)
            coaching_revenue = coaching_clients_total * coaching_price
            deal_revenue = sum(commission_schedule)
            total_revenue = coaching_revenue + deal_revenue
            total_expense = total_monthly_expense * months
            net_profit = total_revenue - total_expense

            if net_profit >= net_target:
                # Flatten deal plan
                flattened = []
                for month_deals in deal_plan:
                    for val, rate in month_deals:
                        flattened.append((val, rate))

                results.append({
                    "Total Coaching Clients": coaching_clients_total,
                    "Total Coaching Revenue": coaching_revenue,
                    "Total Deal Revenue": round(deal_revenue, 2),
                    "Net Profit": round(net_profit, 2),
                    "Total Revenue": round(total_revenue, 2),
                    "Deal Plan (Flat)": ",".join([f"{val},{rate}" for val, rate in flattened])
                })

        percent_complete = (batch + 1) / runs
        progress_bar.progress(percent_complete)
        status_placeholder.text(f"Processed batch {batch + 1} of {runs}")

    # -------------------------
    # DISPLAY RESULTS
    # -------------------------
    if results:
        st.success(f"✅ Found {len(results)} qualifying scenarios")
        df = pd.DataFrame(results)
        df = df.sort_values(by="Net Profit", ascending=False).reset_index(drop=True)
        st.dataframe(df.head(100))

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Results as CSV", data=csv, file_name="forecast_results.csv", mime="text/csv")
    else:
        st.warning("❗ No combinations reached the net profit target. Try adjusting your parameters.")

    st.write(f"⏱️ Total runtime: {round(time.time() - start_time, 2)} seconds")
