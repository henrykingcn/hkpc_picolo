"""
Check what classes the YOLO model has
"""
from ultralytics import YOLO

print("Loading YOLO model...")
model = YOLO("yolo10s.pt")

print("\nModel class names:")
print("=" * 60)
for idx, name in model.names.items():
    print(f"{idx}: {name}")

print("=" * 60)
print(f"\nTotal classes: {len(model.names)}")



