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
    for i in st.session_state.car_
