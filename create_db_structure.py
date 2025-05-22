import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.firestore import SERVER_TIMESTAMP
import random


# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")  # Download from Firebase Project Settings
firebase_admin.initialize_app(cred)
db = firestore.client()

def setup_firestore():
    
    for product in products:
        db.collection("products").add(product)
    
    # 2. Create Default Cart
    db.collection("carts").document("current").set({
        "userID": "default",
        "items": [],
        "status": "active"
    })
    
    print("🔥 Firebase setup completed successfully!")


def add_products():
    # List of unique product names with prices in rupees
    products = [
        {"name": "amul_darkchocolate", "price": 50},
        {"name": "balaji_aloo_sev", "price": 20},
        {"name": "balaji_ratlami_sev", "price": 25},
        {"name": "balaji_wafers_chaatchaska", "price": 30},
        {"name": "balaji_wafers_masalamasti", "price": 30},
        {"name": "balaji_wafers_simplysalted", "price": 30},
        {"name": "balaji_wafers_tomatotwist", "price": 30},
        {"name": "britannia_marie_gold", "price": 35},
        {"name": "cadbury_celebrations", "price": 150},
        {"name": "closeup", "price": 45},
        {"name": "colgate_strong_teeth", "price": 75},
        {"name": "dark_fantasy_choco_fills", "price": 40},
        {"name": "dove_shampoo", "price": 180},
        {"name": "dove_soap", "price": 45},
        {"name": "everest_chaat_masala", "price": 55},
        {"name": "everest_garam_masala", "price": 60},
        {"name": "head_and_shoulders", "price": 190},
        {"name": "krack_jack", "price": 10},
        {"name": "lakme_peach_moisturiser", "price": 120},
        {"name": "lifebuoy", "price": 35},
        {"name": "liril_bodywash", "price": 160},
        {"name": "lux", "price": 40},
        {"name": "maggi", "price": 14},
        {"name": "nescafe_coffee", "price": 200},
        {"name": "patanjali_aloevera_gel", "price": 85},
        {"name": "pears", "price": 50},
        {"name": "real_grape_juice", "price": 90},
        {"name": "rin_soap", "price": 30},
        {"name": "shreeji_dabeli_masala", "price": 40},
        {"name": "shreeji_undhiyu_masala", "price": 45},
        {"name": "surf_excel", "price": 150},
        {"name": "tata_salt", "price": 25},
        {"name": "tresemme_black", "price": 220},
        {"name": "vaseline_aloe_fresh", "price": 95},
        {"name": "veg_hakka_noodles", "price": 45},
        {"name": "vicco_vajradanti", "price": 65},
        {"name": "vim_bar", "price": 20}
    ]
    
    for product in products:
        # Generate a random 9-digit barcode
        barcode = str(random.randint(100000000, 999999999))
        
        # Add the product to Firestore
        db.collection("products").add({
            "barcode": barcode,
            "name": product["name"],
            "price": product["price"]
        })
    
    print(f"✅ Added {len(products)} products to Firestore successfully!")


if __name__ == "__main__":
    setup_firestore()
    add_products()
    print("🔥Setup completed successfully!")
