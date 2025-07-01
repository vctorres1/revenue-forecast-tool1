import streamlit as st
import pandas as pd
import random
import itertools

st.set_page_config(page_title="Revenue Forecast Simulator", layout="wide")
st.title("EPP 1 Revenue Forecast Simulator")

# -------------------------
# SIDEBAR INPUTS
# -------------------------
st.sidebar.header("Simulation Settings")

months = st.sidebar.slider("Number of Months (Forecast Period)", 1, 12, 6)
net_target = st.sidebar.number_input("Net Profit Target", value=1_000_000)
coaching_price = st.sidebar.number_input("Coaching Price per Engagement", value=8750)
total_deal_plans = st.sidebar.number_input("Total Number of Deal Plans to Simulate", value=100_000, step=10000)
batch_size = st.sidebar.number_input("Batch Size (for simulation)", value=5000, step=1000)

# Deal Range (per month)
min_deals = st.sidebar.number_input("Min Deals per Month", value=0)
max_deals = st.sidebar.number_input("Max Deals per Month", value=3)
deal_range = list(range(min_deals, max_deals + 1))

# Deal Values
st.sidebar.subheader("Deal Values")
deal_values = st.sidebar.multiselect(
    "Select Deal Values", 
    [500_000, 1_000_000, 1_500_000, 2_000_000, 2_500_000], 
    default=[500_000, 1_500_000, 2_500_000]
)

# Map realistic commission rates for each deal value
deal_commission_map = {
    500_000: [0.11, 0.13, 0.17],
    1_000_000: [0.07, 0.11, 0.13],
    1_500_000: [0.05, 0.07, 0.11],
    2_000_000: [0.05, 0.07],
    2_500_000: [0.05, 0.07]
}

# Filter mapping to selected deal values
deal_commission_map = {k: deal_commission_map[k] for k in deal_values}

# -------------------------
# EXPENSE SECTION
# -------------------------
st.markdown("## Monthly Expenses")

# Default line items
default_expenses = [
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

if "expenses" not in st.session_state:
    st.session_state.expenses = default_expenses

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
# SIMULATION BUTTON
# -------------------------
if st.button("Run Simulation"):
    st.info("Running simulation, please wait...")

    qualified_results = []
    near_qualified_results = []

    # Generate deal options using value-specific commission ranges
    all_monthly_options = []
    for value, rates in deal_commission_map.items():
        for rate in rates:
            for count in deal_range:
                all_monthly_options.append((count, value, rate))

    progress_bar = st.progress(0)
    total_batches = total_deal_plans // batch_size

    for b in range(total_batches):
        batch_deal_plans = [tuple(random.choices(all_monthly_options, k=months)) for _ in range(batch_size)]

        for d_plan in batch_deal_plans:
            monthly_commission_2025 = [0] * months
            for i, (deal_count, deal_value, commission_rate) in enumerate(d_plan):
                if deal_count == 0:
                    continue
                commission_per_deal = deal_value * commission_rate
                total_commission = deal_count * commission_per_deal
                monthly_payment = total_commission / 12
                for j in range(i + 2, i + 14):
                    if j >= months:
                        break
                    monthly_commission_2025[j] += monthly_payment

            commission_revenue = sum(monthly_commission_2025)
            total_expenses = total_expense_per_month * months
            for coaching_clients in range(0, 11):
                coaching_revenue = coaching_clients * coaching_price
                total_revenue = coaching_revenue + commission_revenue
                net_profit = total_revenue - total_expenses

                if net_profit >= net_target:
                    qualified_results.append({
                        "Total Coaching Clients": coaching_clients,
                        "Deal Plan": ",".join(f"{x[0]},{x[1]},{x[2]}" for x in d_plan),
                        "Coaching Revenue": coaching_revenue,
                        "Deal Revenue (2025)": commission_revenue,
                        "Total Revenue": total_revenue,
                        "Net Profit": net_profit,
                        "Workload": coaching_clients + sum(d[0] for d in d_plan)
                    })
                    break  # Stop once it qualifies
                elif net_profit >= 800_000:
                    near_qualified_results.append({
                        "Total Coaching Clients": coaching_clients,
                        "Deal Plan": ",".join(f"{x[0]},{x[1]},{x[2]}" for x in d_plan),
                        "Coaching Revenue": coaching_revenue,
                        "Deal Revenue (2025)": commission_revenue,
                        "Total Revenue": total_revenue,
                        "Net Profit": net_profit,
                        "Workload": coaching_clients + sum(d[0] for d in d_plan)
                    })
                    break

        progress_bar.progress((b + 1) / total_batches)

    # -------------------------
    # RESULTS
    # -------------------------
    st.subheader("Qualified Plans (≥ $1M Net Profit)")
    if qualified_results:
        df1 = pd.DataFrame(qualified_results).sort_values(by=["Workload", "Net Profit"], ascending=[True, False])
        st.dataframe(df1.head(100))
        csv1 = df1.to_csv(index=False).encode("utf-8")
        st.download_button("Download Qualified Results as CSV", data=csv1, file_name="qualified_forecasts.csv")
    else:
        st.warning("No qualified plans found.")

    st.subheader("Near-Qualified Plans (≥ $800K Net Profit)")
    if near_qualified_results:
        df2 = pd.DataFrame(near_qualified_results).sort_values(by=["Workload", "Net Profit"], ascending=[True, False])
        st.dataframe(df2.head(100))
        csv2 = df2.to_csv(index=False).encode("utf-8")
        st.download_button("Download Near-Qualified Results as CSV", data=csv2, file_name="near_qualified_forecasts.csv")
    else:
        st.warning("No near-qualified plans found.")
