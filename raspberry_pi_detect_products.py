import cv2
import numpy as np
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import time
from ultralytics import YOLO
import RPi.GPIO as GPIO

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# LED pins
GREEN_LED = 17  # New item added
BLUE_LED = 27   # Quantity updated
RED_LED = 22    # No detection

# Setup GPIO pins
GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(BLUE_LED, GPIO.OUT)
GPIO.setup(RED_LED, GPIO.OUT)

# Initialize all LEDs to off
GPIO.output(GREEN_LED, GPIO.LOW)
GPIO.output(BLUE_LED, GPIO.LOW)
GPIO.output(RED_LED, GPIO.LOW)

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize YOLO model
model = YOLO('honey.pt')

# Create a list of all product base names from your database
BASE_NAMES = [
    "amul_darkchocolate", "balaji_aloo_sev", "balaji_ratlami_sev", 
    "balaji_wafers_chaatchaska", "balaji_wafers_masalamasti",
    "balaji_wafers_simplysalted", "balaji_wafers_tomatotwist",
    "britannia_marie_gold", "cadbury_celebrations", "closeup",
    "colgate_strong_teeth", "dark_fantasy_choco_fills", "dove_shampoo",
    "dove_soap", "everest_chaat_masala", "everest_garam_masala",
    "head_and_shoulders", "krack_jack", "lakme_peach_moisturiser",
    "lifebuoy", "liril_bodywash", "lux", "maggi", "nescafe_coffee",
    "patanjali_aloevera_gel", "pears", "real_grape_juice", "rin_soap",
    "shreeji_dabeli_masala", "shreeji_undhiyu_masala", "surf_excel",
    "tata_salt", "tresemme_black", "vaseline_aloe_fresh",
    "veg_hakka_noodles", "vicco_vajradanti", "vim_bar"
]

# Pre-sort the base names by length (longest first) for more efficient matching
BASE_NAMES_SORTED = sorted(BASE_NAMES, key=len, reverse=True)

CLASS_NAME_MAP = {}
for class_id, name in model.names.items():
    # Find the longest matching base name
    matched_name = None
    for base_name in BASE_NAMES_SORTED:
        if name.startswith(base_name):
            matched_name = base_name
            break
    
    # If no match found, fall back to first two parts
    if matched_name is None:
        parts = name.split('_')
        matched_name = '_'.join(parts[:2])
    
    CLASS_NAME_MAP[class_id] = matched_name

# Track recently detected objects
last_detection_time = 0  # Track the last time any product was added
cooldown_period = 2.0    # 2 seconds cooldown after adding a product

def blink_led(pin, duration=0.5):
    """Blink an LED for a specified duration"""
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(pin, GPIO.LOW)

def lookup_product(name):
    """Search Firebase for product details by name"""
    docs = db.collection("products").where("name", "==", name).get()
    return docs[0].to_dict() if docs else None

def get_category_color(class_id):
    """Color coding for product categories"""
    product_name = CLASS_NAME_MAP.get(class_id, "").lower()
    if 'chocolate' in product_name or 'biscuit' in product_name:
        return (0, 255, 0)  # Green for snacks
    elif 'shampoo' in product_name or 'soap' in product_name:
        return (255, 0, 0)  # Blue for personal care
    return (255, 255, 255)  # Default: White

def add_to_cart(product):
    """Add product with full details to cart or increment quantity if already exists"""
    cart_ref = db.collection("carts").document("current")
    
    try:
        cart = cart_ref.get()
        if cart.exists:
            items = cart.to_dict().get("items", [])
            
            found = False
            for item in items:
                if item.get("barcode") == product.get("barcode"):
                    item["quantity"] += 1
                    item["timestamp"] = datetime.now()
                    found = True
                    break
            
            if found:
                cart_ref.update({"items": items})
                print(f"➕ Updated quantity for: {product['name']}")
                blink_led(BLUE_LED)  # Blue LED for quantity update
            else:
                new_item = {
                    "barcode": product.get("barcode", ""),
                    "name": product["name"],
                    "price": product.get("price", 0),
                    "quantity": 1,
                    "timestamp": datetime.now()
                }
                cart_ref.update({"items": firestore.ArrayUnion([new_item])})
                print(f"✅ Added to cart: {product['name']}")
                blink_led(GREEN_LED)  # Green LED for new item
        else:
            cart_ref.set({
                "items": [{
                    "barcode": product.get("barcode", ""),
                    "name": product["name"],
                    "price": product.get("price", 0),
                    "quantity": 1,
                    "timestamp": datetime.now()
                }]
            })
            print(f"✅ Created cart with: {product['name']}")
            blink_led(GREEN_LED)  # Green LED for new item
    except Exception as e:
        print(f"❌ Error updating cart: {e}")

def process_frame(frame):
    """Detect products and manage cart additions with cooldown"""
    global last_detection_time
    
    current_time = time.time()
    
    # Check if we're in cooldown period
    if current_time - last_detection_time < cooldown_period:
        return frame
    
    results = model(frame, verbose=False)
    
    # Turn on red LED if no detections
    if len(results[0].boxes) == 0:
        GPIO.output(RED_LED, GPIO.HIGH)
    else:
        GPIO.output(RED_LED, GPIO.LOW)
    
    # Process detections with highest confidence first
    detections = []
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
            class_id = int(box.cls[0])
            conf = float(box.conf[0])
            detections.append((conf, class_id, (x1, y1, x2, y2)))
    
    # Sort detections by confidence (highest first)
    detections.sort(reverse=True, key=lambda x: x[0])
    
    for conf, class_id, (x1, y1, x2, y2) in detections:
        product_name = CLASS_NAME_MAP.get(class_id, f"ID {class_id}")
        color = get_category_color(class_id)
        
        # Draw bounding box for visualization
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{product_name} {conf:.2f}", (x1, y1 - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Only process for cart if confidence is high enough
        if conf > 0.5:
            product = lookup_product(product_name)
            if product:
                # Immediately add to cart
                add_to_cart(product)
                # Set cooldown period
                last_detection_time = time.time()
                # Break after first high-confidence detection to avoid multiple additions
                break
    
    return frame

def main():
    # Camera initialization
    found = False
    for index in range(3):  # Try index 0, 1, 2
        for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
            cap = cv2.VideoCapture(index,  backend)
            if cap.isOpened():
                print(f"Camera found at index {index} using backend: {backend}")
                found = True
                break
            cap.release()
        if found:
            break

    if not found:
        print("Error: Could not open any camera")
        sys.exit(1)
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 15)
    
    print("System ready! Detected products will be added immediately. Press 'q' to quit.")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame, retrying...")
                time.sleep(0.1)
                continue
            
            frame = process_frame(frame)
            cv2.imshow('Product Scanner', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        GPIO.cleanup()

if __name__ == "__main__":
    main()
