import cv2
import time
from ultralytics import YOLO

# Initialize YOLO model
model = YOLO('honey.pt')

# Create a list of all product base names from your original list
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

# Pre-sort base names by length (to match the longest substring first)
BASE_NAMES_SORTED = sorted(BASE_NAMES, key=len, reverse=True)

# Map model class IDs to base names
CLASS_NAME_MAP = {}
for class_id, name in model.names.items():
    matched_name = None
    for base_name in BASE_NAMES_SORTED:
        if name.startswith(base_name):
            matched_name = base_name
            break
    if matched_name is None:
        parts = name.split('_')
        matched_name = '_'.join(parts[:2])
    CLASS_NAME_MAP[class_id] = matched_name

def get_category_color(class_id):
    """Color code for categories"""
    name = CLASS_NAME_MAP.get(class_id, "").lower()
    if 'chocolate' in name or 'biscuit' in name:
        return (0, 255, 0)  # Green
    elif 'shampoo' in name or 'soap' in name:
        return (255, 0, 0)  # Blue
    return (255, 255, 255)  # White

def process_frame(frame):
    """Detect and label products"""
    results = model(frame, verbose=False)

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
            class_id = int(box.cls[0])
            conf = float(box.conf[0])

            product_name = CLASS_NAME_MAP.get(class_id, f"ID {class_id}")
            color = get_category_color(class_id)

            # Draw bounding box and label
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"{product_name} {conf:.2f}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    return frame

def main():
    cap = None
    for index in range(3):
        for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
            cap = cv2.VideoCapture(index, backend)
            if cap.isOpened():
                print(f"✅ Camera found at index {index} using backend {backend}")
                break
            cap.release()
        if cap and cap.isOpened():
            break

    if not cap or not cap.isOpened():
        print("❌ Could not open any camera.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    print("🎯 Model detection active. Press 'q' to quit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("⚠️ Frame grab failed.")
                continue

            frame = process_frame(frame)
            cv2.imshow("Product Detection", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
