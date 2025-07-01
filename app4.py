import streamlit as st
import pandas as pd
import itertools
import random

# -------------------------
# PAGE SETUP
# -------------------------
st.set_page_config(page_title="EPP Revenue Forecast Simulator", layout="wide")
st.title("EPP 1 Revenue Forecast Simulator")

# -------------------------
# SIDEBAR INPUTS
# -------------------------
st.sidebar.header("Simulation Settings")

months = st.sidebar.slider("Forecast Period (Months)", 1, 12, 6)
net_target = st.sidebar.number_input("Net Profit Target", value=1_000_000)
near_target_threshold = st.sidebar.number_input("Near-Target Threshold", value=800_000)
coaching_price = st.sidebar.number_input("Coaching Price per Engagement", value=8750)

max_coaching_per_month = st.sidebar.number_input("Max Coaching Clients Per Month", value=5, min_value=0)

deal_values = st.sidebar.multiselect("Deal Values", [500_000, 1_000_000, 1_500_000, 2_000_000, 2_500_000], default=[500_000, 1_500_000, 2_500_000])
commission_rates = st.sidebar.multiselect("Commission Rates", [0.05, 0.07, 0.11, 0.13, 0.17], default=[0.05, 0.11, 0.17])

batch_size = st.sidebar.number_input("Simulation Batch Size", value=500, min_value=100)
max_iterations = st.sidebar.number_input("Max Simulation Steps", value=50, min_value=1)

# -------------------------
# DEFAULT EXPENSES
# -------------------------
st.subheader("Monthly Expenses")
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

monthly_expense = sum(exp["amount"] for exp in st.session_state.expenses)
st.markdown(f"**Total Monthly Expense:** ${monthly_expense:,.2f}")

# -------------------------
# RUN SIMULATION
# -------------------------
if st.button("Run Simulation"):
    results_qualified = []
    results_near = []

    deal_options = list(itertools.product(deal_values, commission_rates))

    progress = st.progress(0, text="Building monthly plans...")
    for step in range(max_iterations):
        progress.progress(step / max_iterations, f"Step {step + 1}/{max_iterations}")

        monthly_plan = []
        total_coaching = 0
        total_commission_stream = [0] * months

        for m in range(months):
            coaching_clients = random.randint(0, max_coaching_per_month)
            total_coaching += coaching_clients

            current_month_deals = random.sample(deal_options, k=min(len(deal_options), 3))
            deal_mix = []
            for deal_value, rate in current_month_deals:
                count = random.randint(0, 2)
                if count == 0:
                    continue
                commission = deal_value * rate * count
                monthly_payment = commission / 12
                for future_m in range(m + 2, m + 14):
                    if future_m < months:
                        total_commission_stream[future_m] += monthly_payment
                deal_mix.append((count, deal_value, rate))

            monthly_plan.append({
                "month": m + 1,
                "coaching_clients": coaching_clients,
                "deals": deal_mix
            })

        coaching_revenue = total_coaching * coaching_price
        commission_revenue = sum(total_commission_stream)
        total_revenue = coaching_revenue + commission_revenue
        total_expenses = monthly_expense * months
        net_profit = total_revenue - total_expenses

        result = {
            "Monthly Plan": monthly_plan,
            "Coaching Revenue": coaching_revenue,
            "Deal Revenue (2025)": commission_revenue,
            "Total Revenue": round(total_revenue, 2),
            "Net Profit": round(net_profit, 2),
            "Total Coaching Clients": total_coaching,
            "Total Expense": total_expenses
        }

        if net_profit >= net_target:
            results_qualified.append(result)
        elif net_profit >= near_target_threshold:
            results_near.append(result)

    progress.empty()

    # -------------------------
    # DISPLAY RESULTS
    # -------------------------
    def flatten_plan(plan):
        return ",".join(
            f"M{p['month']}|C{p['coaching_clients']}|" +
            "|".join([f"{d[0]}x{d[1]}@{int(d[2]*100)}%" for d in p['deals']])
            for p in plan
        )

    def display_results(label, data):
        if not data:
            return
        st.subheader(f"{label} ({len(data)} found)")
        df = pd.DataFrame(data)
        df["Plan Summary"] = df["Monthly Plan"].apply(flatten_plan)
        df_display = df[["Plan Summary", "Coaching Revenue", "Deal Revenue (2025)", "Total Revenue", "Total Expense", "Net Profit", "Total Coaching Clients"]]
        st.dataframe(df_display.head(100), use_container_width=True)

        csv = df_display.to_csv(index=False).encode("utf-8")
        st.download_button(f"Download {label} as CSV", data=csv, file_name=f"{label.lower().replace(' ', '_')}.csv")

    if results_qualified:
        display_results("Qualified Plans (≥ $1M Net Profit)", results_qualified)
    else:
        st.warning("No qualified plans found.")

    if results_near:
        display_results("Near-Qualified Plans (≥ $800K Net Profit)", results_near)
