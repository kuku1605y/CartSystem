from ultralytics import YOLO

# Load your trained model
model = YOLO('honey.pt')

# Print class names
print(model.names)
