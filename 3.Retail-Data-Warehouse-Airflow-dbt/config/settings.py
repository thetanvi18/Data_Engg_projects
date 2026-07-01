"""
config/settings.py
──────────────────
Central config for DB connections and project-wide constants.
Reads from environment variables (set via .env or Docker Compose).
"""
import os

# ── Database ──────────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DW_HOST",     "localhost"),
    "port":     int(os.getenv("DW_PORT", "5432")),
    "user":     os.getenv("DW_USER",     "retail_user"),
    "password": os.getenv("DW_PASSWORD", "retail_pass"),
    "dbname":   os.getenv("DW_DB",       "retail_dw"),
}

# ── Data generation volumes ────────────────────────────────────────────────────
NUM_CUSTOMERS   = int(os.getenv("NUM_CUSTOMERS",   "5000"))
NUM_PRODUCTS    = int(os.getenv("NUM_PRODUCTS",    "500"))
NUM_ORDERS      = int(os.getenv("NUM_ORDERS",      "20000"))
NUM_PAYMENTS    = NUM_ORDERS          # 1 payment per order
NUM_INVENTORY   = NUM_PRODUCTS        # 1 inventory record per product
ITEMS_PER_ORDER = 2.5                 # average; total ~50k rows

# ── Dirty-data injection rates ─────────────────────────────────────────────────
NULL_EMAIL_RATE         = 0.05   # 5%  of customers have no email
BAD_PHONE_RATE          = 0.08   # 8%  of customers have malformed phone
MIXED_CASE_CITY_RATE    = 0.10   # 10% of customers have inconsistent city casing
DUPLICATE_ORDER_RATE    = 0.015  # 1.5% duplicate order rows
FUTURE_DATE_RATE        = 0.01   # 1%  of orders have a future order_date
NEGATIVE_QTY_RATE       = 0.01   # 1%  of order_items are returns (negative qty)
ORPHAN_ITEM_RATE        = 0.005  # 0.5% of order_items have no matching order
ZERO_PAYMENT_RATE       = 0.01   # 1%  of payments have amount = 0
ZERO_PRICE_RATE         = 0.03   # 3%  of products have unit_price = 0
NEGATIVE_INVENTORY_RATE = 0.05   # 5%  of inventory records have qty < 0

# ── Faker seed ────────────────────────────────────────────────────────────────
FAKER_SEED   = 42
RANDOM_SEED  = 42

# ── Reference data ────────────────────────────────────────────────────────────
CATEGORIES = [
    ("Electronics",    ["Smartphones", "Laptops", "Tablets", "Headphones", "Cameras"]),
    ("Clothing",       ["Men's Wear", "Women's Wear", "Kids Wear", "Sportswear", "Accessories"]),
    ("Home & Kitchen", ["Cookware", "Furniture", "Bedding", "Appliances", "Decor"]),
    ("Books",          ["Fiction", "Non-Fiction", "Academic", "Children's", "Comics"]),
    ("Sports",         ["Cricket", "Football", "Fitness", "Outdoor", "Swimming"]),
    ("Beauty",         ["Skincare", "Haircare", "Makeup", "Fragrances", "Personal Care"]),
    ("Grocery",        ["Staples", "Snacks", "Beverages", "Dairy", "Organic"]),
    ("Toys",           ["Action Figures", "Board Games", "Educational", "Outdoor Toys", "Dolls"]),
]

BRANDS = [
    "RetailCo", "ShopMart", "MegaStore", "BrandX", "ValuePlus",
    "PremiumHub", "TrendyBuy", "SmartShop", "QuickBuy", "DealZone",
]

PAYMENT_METHODS   = ["Credit Card", "Debit Card", "UPI", "Net Banking", "Wallet", "COD"]
ORDER_STATUSES    = ["Pending", "Processing", "Shipped", "Delivered", "Cancelled", "Returned"]
SHIPPING_METHODS  = ["Standard", "Express", "Overnight", "Free Shipping"]
CUSTOMER_SEGMENTS = ["Premium", "Regular", "Budget", "VIP"]
WAREHOUSES        = ["Mumbai-Central", "Mumbai-West", "Thane", "Pune", "Delhi", "Bangalore"]

CITY_CASING_VARIANTS = {
    "Mumbai":    ["mumbai", "MUMBAI", "Mumbai"],
    "Delhi":     ["delhi",  "DELHI",  "Delhi"],
    "Bangalore": ["bangalore", "BANGALORE", "Bangalore"],
    "Pune":      ["pune",   "PUNE",   "Pune"],
    "Chennai":   ["chennai","CHENNAI","Chennai"],
    "Hyderabad": ["hyderabad","HYDERABAD","Hyderabad"],
    "Kolkata":   ["kolkata","KOLKATA","Kolkata"],
    "Ahmedabad": ["ahmedabad","AHMEDABAD","Ahmedabad"],
}
