# MAGNATE POS (Streamlit)

Simple Point-of-Sale system built with Streamlit.
Features:
- Inventory management (Category, Supplier, Cost price, Selling price, Wholesale price, Stock, Reorder level, Expiry, Barcode, UOM, Notes)
- Cart & Checkout
- Receipt preview with logo
- PDF receipt generation (reportlab) with logo embedded
- CSV export of sales

## Requirements
- Python 3.9+
- The repository files:
  - `app.py`
  - `magnate_logo.png` (your company logo)
  - `requirements.txt`

## Setup
1. Create & activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   .venv\\Scripts\\activate    # Windows (PowerShell)
