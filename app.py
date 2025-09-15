import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="POS System", layout="wide")

# --- Initialize session state ---
if "products" not in st.session_state:
    st.session_state.products = pd.DataFrame([
        {"id": "p1", "sku": "1001", "name": "Orthopedic Knee Brace", "price": 2500, "stock": 10},
        {"id": "p2", "sku": "1002", "name": "Spine Support Belt", "price": 1800, "stock": 8},
        {"id": "p3", "sku": "1003", "name": "Ankle Walker", "price": 3200, "stock": 5},
    ])

if "cart" not in st.session_state:
    st.session_state.cart = []

if "sales" not in st.session_state:
    st.session_state.sales = []

# --- Utility Functions ---
def add_to_cart(product, qty=1):
    for item in st.session_state.cart:
        if item["id"] == product["id"]:
            item["qty"] += qty
            return
    st.session_state.cart.append({**product, "qty": qty})

def remove_from_cart(pid):
    st.session_state.cart = [i for i in st.session_state.cart if i["id"] != pid]

def update_qty(pid, qty):
    for i in st.session_state.cart:
        if i["id"] == pid:
            i["qty"] = max(1, qty)

def subtotal():
    return sum(i["price"] * i["qty"] for i in st.session_state.cart)

def checkout(customer, payment):
    if not st.session_state.cart:
        st.warning("Cart is empty!")
        return
    sale = {
        "id": f"s_{len(st.session_state.sales)+1}",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer": customer or "Walk-in",
        "payment": payment,
        "items": st.session_state.cart.copy(),
        "total": subtotal()
    }
    # Reduce stock
    for item in st.session_state.cart:
        st.session_state.products.loc[
            st.session_state.products["id"] == item["id"], "stock"
        ] -= item["qty"]
    st.session_state.sales.insert(0, sale)
    st.session_state.cart = []
    st.success(f"Sale completed! Receipt #{sale['id']}")

# --- Layout ---
st.title("💳 Point of Sale (Streamlit)")

tabs = st.tabs(["🛍️ Products", "🛒 Cart", "📊 Reports"])

# --- Products tab ---
with tabs[0]:
    st.subheader("Available Products")
    search = st.text_input("Search products", "")
    df = st.session_state.products
    if search:
        df = df[df["name"].str.contains(search, case=False) | df["sku"].str.contains(search)]
    st.dataframe(df, use_container_width=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        pid = st.selectbox("Select product", df["id"])
        qty = st.number_input("Quantity", 1, 100, 1)
    with col2:
        if st.button("Add to Cart"):
            product = df[df["id"] == pid].iloc[0].to_dict()
            add_to_cart(product, qty)

# --- Cart tab ---
with tabs[1]:
    st.subheader("Cart")
    if not st.session_state.cart:
        st.info("Cart is empty")
    else:
        for item in st.session_state.cart:
            cols = st.columns([3, 2, 2, 1])
            cols[0].write(item["name"])
            cols[1].write(f"KES {item['price']:,}")
            qty = cols[2].number_input("Qty", 1, item["stock"], item["qty"], key=item["id"])
            update_qty(item["id"], qty)
            if cols[3].button("❌", key="rm_" + item["id"]):
                remove_from_cart(item["id"])
                st.rerun()
        st.markdown("---")
        st.write(f"**Subtotal:** KES {subtotal():,}")

        with st.expander("Checkout"):
            customer = st.text_input("Customer Name", "")
            payment = st.selectbox("Payment Method", ["Cash", "Card", "Mobile Money"])
            if st.button("Confirm Payment"):
                checkout(customer, payment)

# --- Reports tab ---
with tabs[2]:
    st.subheader("Sales Reports")
    if not st.session_state.sales:
        st.info("No sales yet")
    else:
        df_sales = pd.DataFrame([
            {"id": s["id"], "date": s["date"], "customer": s["customer"], "payment": s["payment"], "total": s["total"]}
            for s in st.session_state.sales
        ])
        st.dataframe(df_sales, use_container_width=True)
        st.write(f"**Total Sales:** KES {df_sales['total'].sum():,}")
        st.download_button("⬇️ Export CSV", df_sales.to_csv(index=False), "sales.csv")
