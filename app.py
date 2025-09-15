import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A6, landscape, letter
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
import os

st.set_page_config(page_title="MAGNATE POS", layout="wide")

# --- Helper: load local logo path ---
LOGO_FILENAME = "magnate_logo.png"
logo_exists = os.path.exists(LOGO_FILENAME)

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

def save_sale_and_reduce_stock(sale):
    # Reduce stock in the product dataframe
    for item in sale["items"]:
        st.session_state.products.loc[
            st.session_state.products["id"] == item["id"], "stock"
        ] -= item["qty"]
    st.session_state.sales.insert(0, sale)

def generate_pdf_receipt(sale):
    """
    Returns PDF bytes for a receipt that includes the logo (if present),
    sale details and itemized list.
    """
    buffer = io.BytesIO()
    # Use a compact page size suitable for receipts; letter rotated or A6 can be used.
    # We'll use portrait A6 (small receipt) but use letter width for compatibility if needed.
    PAGE_WIDTH, PAGE_HEIGHT = 210 * mm, 297 * mm  # A4 portrait defaults (we'll draw compactly)
    c = canvas.Canvas(buffer, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    x_margin = 15 * mm
    y = PAGE_HEIGHT - 20 * mm

    # Draw logo if available
    if logo_exists:
        try:
            img = ImageReader(LOGO_FILENAME)
            # scale to width 40mm while keeping aspect ratio
            img_w, img_h = img.getSize()
            draw_w = 40 * mm
            draw_h = draw_w * (img_h / img_w)
            c.drawImage(img, x_margin, y - draw_h, width=draw_w, height=draw_h, preserveAspectRatio=True, mask='auto')
            logo_x_end = x_margin + draw_w + 5 * mm
        except Exception:
            logo_x_end = x_margin
    else:
        logo_x_end = x_margin

    # Header text
    c.setFont("Helvetica-Bold", 14)
    c.drawString(logo_x_end, y - 6 * mm, "MAGNATE 001")
    c.setFont("Helvetica", 9)
    c.drawString(logo_x_end, y - 12 * mm, "Official Point of Sale")
    c.setFont("Helvetica", 8)
    y = y - 30 * mm

    # Sale meta
    c.drawString(x_margin, y, f"Receipt #: {sale['id']}")
    c.drawRightString(PAGE_WIDTH - x_margin, y, f"Date: {sale['date']}")
    y -= 6 * mm
    c.drawString(x_margin, y, f"Customer: {sale['customer']}")
    c.drawString(x_margin + 80 * mm, y, f"Payment: {sale['payment']}")
    y -= 8 * mm

    # Line
    c.line(x_margin, y, PAGE_WIDTH - x_margin, y)
    y -= 6 * mm

    # Table header
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_margin, y, "Item")
    c.drawRightString(PAGE_WIDTH - x_margin - 50 * mm, y, "Qty")
    c.drawRightString(PAGE_WIDTH - x_margin - 30 * mm, y, "Price")
    c.drawRightString(PAGE_WIDTH - x_margin, y, "Total")
    y -= 6 * mm
    c.setFont("Helvetica", 9)

    # Items
    for it in sale["items"]:
        name = it["name"]
        qty = it["qty"]
        price = it["price"]
        total = qty * price
        # wrap the name if too long (simple)
        max_name_len = 35
        if len(name) > max_name_len:
            name_lines = [name[i:i+max_name_len] for i in range(0, len(name), max_name_len)]
        else:
            name_lines = [name]
        for line in name_lines:
            c.drawString(x_margin, y, line)
            y -= 5 * mm
        # qty and totals on last line for the item
        c.drawRightString(PAGE_WIDTH - x_margin - 50 * mm, y + (5 * mm * (len(name_lines))), str(qty))
        c.drawRightString(PAGE_WIDTH - x_margin - 30 * mm, y + (5 * mm * (len(name_lines))), f"{price:,}")
        c.drawRightString(PAGE_WIDTH - x_margin, y + (5 * mm * (len(name_lines))), f"{total:,}")
        y -= 2 * mm

        # check space, new page if needed
        if y < 40 * mm:
            c.showPage()
            y = PAGE_HEIGHT - 20 * mm

    y -= 8 * mm
    c.line(x_margin, y, PAGE_WIDTH - x_margin, y)
    y -= 8 * mm

    # Totals
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(PAGE_WIDTH - x_margin - 30 * mm, y, "TOTAL:")
    c.drawRightString(PAGE_WIDTH - x_margin, y, f"KES {sale['total']:,}")
    y -= 10 * mm

    # Footer
    c.setFont("Helvetica", 8)
    c.drawString(x_margin, y, "Thank you for your purchase!")
    y -= 5 * mm
    c.drawString(x_margin, y, "MAGNATE — Quality orthopedic supplies")
    # finish
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

def checkout_and_publish_pdf(customer, payment):
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

    save_sale_and_reduce_stock(sale)
    st.session_state.cart = []

    # show on-screen receipt
    st.success(f"✅ Sale completed! Receipt #{sale['id']}")
    st.markdown("---")
    if logo_exists:
        st.image(LOGO_FILENAME, width=120)
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

    # generate PDF and provide download
    try:
        pdf_bytes = generate_pdf_receipt(sale)
        st.download_button(
            label="⬇️ Download PDF Receipt",
            data=pdf_bytes,
            file_name=f"receipt_{sale['id']}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error("Could not generate PDF receipt. Make sure reportlab is installed and logo file is accessible.")
        st.exception(e)

# --- Layout ---
if logo_exists:
    st.image(LOGO_FILENAME, width=150)
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
                checkout_and_publish_pdf(customer, payment)

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
        # set expiry default to today if None
        expiry_val = row["expiry"] if (pd.notna(row["expiry"]) and row["expiry"] is not None) else date.today()
        new_expiry = expiry_col.date_input("Expiry", value=expiry_val, key=f"exp_{row['id']}")

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
