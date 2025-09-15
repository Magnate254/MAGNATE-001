import streamlit as st
import pandas as pd
from datetime import datetime, date

st.set_page_config(page_title="MAGNATE POS", layout="wide")

# --- Initialize session state ---
if "products" not in st.session_state:
    st.session_state.products = pd.DataFrame([
        {
            "id": "p1", "sku": "1001", "name": "Orthopedic Knee Brace",
            "category": "Braces", "supplier": "MedSupplies Ltd",
            "cost_price": 1500, "price": 2500, "wholesale_price": 2200,
            "stock": 10, "reorder_level": 5, "expiry": None,
            "barcode": "111111", "uom": "Piece", "notes": "Adjustable size"
        },
        {
            "id": "p2", "sku": "1002", "name": "Spine Support Belt",
            "category": "Supports", "supplier": "OrthoImports",
            "cost_price": 1200, "price": 1800, "wholesale_price": 1500,
            "stock": 8, "reorder_level": 3, "expiry": None,
            "barcode": "222222", "uom": "Piece", "notes": ""
        },
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

    # Receipt Preview
    st.success(f"✅ Sale completed! Receipt #{sale['id']}")
    st.markdown("---")
    st.image("magnate_logo.png", width=120)   # <-- place your logo file here
    st.markdown("### MAGNATE 001")
    st.markdown("**Official Receipt**")
    st.write(f"Date: {sale['date']}")
    st.write(f"Customer: {sale['customer']}")
    st.write(f"Payment Method: {sale['payment']}")
    st.markdown("---")

    for item in sale["items"]:
        st.write(f"{item['name']} x {item['qty']} — KES {item['price'] * item['qty']:,}")

    st.markdown("---")
    st.write(f"**TOTAL: KES {sale['total']:,}**")

# --- Layout ---
st.image("magnate_logo.png", width=150)   # App letterhead logo
st.title("💳 MAGNATE POS SYSTEM")
st.markdown("**MAGNATE 001** — Official Point of Sale")

tabs = st.tabs(["🛍️ Products", "🛒 Cart", "📦 Inventory", "📊 Reports"])

# --- Products tab ---
with tabs[0]:
    st.subheader("Available Products")
    search = st.text_input("Search products", "")
    df = st.session_state.products
    if search:
        df = df[df["name"].str.contains(search, case=False) | df["sku"].str.contains(search)]
    st.dataframe(df[["sku", "name", "price", "stock"]], use_container_width=True)

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

# --- Inventory tab ---
with tabs[2]:
    st.subheader("Inventory Management")
    df = st.session_state.products.copy()

    for idx, row in df.iterrows():
        st.markdown(f"### {row['name']} (SKU: {row['sku']})")
        cols = st.columns([2, 2, 2, 2, 2, 2])
        cols[0].write(f"Category: {row['category']}")
        cols[1].write(f"Supplier: {row['supplier']}")
        cols[2].write(f"Cost: KES {row['cost_price']:,}")
        cols[3].write(f"Price: KES {row['price']:,}")
        cols[4].write(f"Wholesale: KES {row['wholesale_price']:,}")
        cols[5].write(f"UOM: {row['uom']}")

        stock_col, reorder_col, expiry_col = st.columns([2,2,2])
        new_stock = stock_col.number_input("Stock", 0, 9999, int(row["stock"]), key=f"stock_{row['id']}")
        new_reorder = reorder_col.number_input("Reorder Level", 0, 1000, int(row["reorder_level"]), key=f"reorder_{row['id']}")
        new_expiry = expiry_col.date_input("Expiry", value=row["expiry"] if row["expiry"] else date.today(), key=f"exp_{row['id']}")

        st.session_state.products.at[idx, "stock"] = new_stock
        st.session_state.products.at[idx, "reorder_level"] = new_reorder
        st.session_state.products.at[idx, "expiry"] = new_expiry

        notes = st.text_area("Notes", value=row["notes"], key=f"notes_{row['id']}")
        st.session_state.products.at[idx, "notes"] = notes

        if st.button("❌ Delete", key=f"del_{row['id']}"):
            st.session_state.products = st.session_state.products.drop(idx)
            st.rerun()
        st.markdown("---")

    st.subheader("➕ Add New Product")
    with st.form("add_product_form"):
        sku = st.text_input("SKU")
        name = st.text_input("Name")
        category = st.selectbox("Category", ["Braces", "Supports", "Implants", "Consumables", "Other"])
        supplier = st.text_input("Supplier")
        cost_price = st.number_input("Cost Price (KES)", 0, 1_000_000, 0)
        price = st.number_input("Selling Price (KES)", 0, 1_000_000, 0)
        wholesale_price = st.number_input("Wholesale Price (KES)", 0, 1_000_000, 0)
        stock = st.number_input("Initial Stock", 0, 1000, 0)
        reorder_level = st.number_input("Reorder Level", 0, 1000, 5)
        expiry_date = st.date_input("Expiry Date")
        barcode = st.text_input("Barcode / QR Code")
        uom = st.selectbox("Unit of Measure", ["Piece", "Box", "Pack", "Set"])
        notes = st.text_area("Notes / Description")
        submitted = st.form_submit_button("Add Product")
        if submitted:
            new_id = f"p{len(st.session_state.products)+1}"
            new_product = {
                "id": new_id, "sku": sku, "name": name, "category": category,
                "supplier": supplier, "cost_price": cost_price, "price": price,
                "wholesale_price": wholesale_price, "stock": stock, "reorder_level": reorder_level,
                "expiry": expiry_date, "barcode": barcode, "uom": uom, "notes": notes
            }
            st.session_state.products = pd.concat(
                [st.session_state.products, pd.DataFrame([new_product])],
                ignore_index=True
            )
            st.success(f"Product {name} added!")

# --- Reports tab ---
with tabs[3]:
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
