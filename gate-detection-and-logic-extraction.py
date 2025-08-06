from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
from google.colab.patches import cv2_imshow

# Load model and image
model = YOLO('/content/drive/MyDrive/EIS/models/model_100epochs_float16.tflite')
image_path = '/content/drive/MyDrive/EIS/handDrawnTest/paint_logic_circuit.jpeg'
img = cv2.imread(image_path)
annotated_img = img.copy()

# Run inference
results = model(img)[0]
class_labels = ['AND', 'NAND', 'NOR', 'NOT', 'OR', 'XNOR', 'XOR']

# === Detect Gates ===
detected_gates = []
for box in results.boxes:
    cls_id = int(box.cls[0])
    confidence = float(box.conf[0])
    x1, y1, x2, y2 = map(int, box.xyxy[0])
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    detected_gates.append({
        "class_id": cls_id,
        "confidence": confidence,
        "bbox": (x1, y1, x2, y2),
        "center": (cx, cy)
    })

# === Sort Gates Left to Right ===
sorted_gates = sorted(detected_gates, key=lambda g: g['bbox'][0])

# === Identify Left-most Gates (Raw Inputs) ===
input_front_threshold = 40
min_x = min(g['center'][0] for g in sorted_gates)
input_front_gates = [idx for idx, g in enumerate(sorted_gates) if g['center'][0] - min_x <= input_front_threshold]

# === Assign Inputs and Outputs ===
input_vars = [chr(ord('A') + i) for i in range(26)]
input_idx = 0
gate_inputs = {}
gate_outputs = {}
output_labels = [f"Y{i+1}" for i in range(len(sorted_gates))]

for idx, gate in enumerate(sorted_gates):
    cls_label = class_labels[gate['class_id']]
    cx, cy = gate['center']
    required_inputs = 1 if cls_label == "NOT" else 2
    assigned_inputs = []

    if idx in input_front_gates:
        for _ in range(required_inputs):
            if input_idx < len(input_vars):
                assigned_inputs.append(input_vars[input_idx])
                input_idx += 1
    else:
        candidate_gates = sorted_gates[:idx]
        candidates = []
        for prev_idx, prev_gate in enumerate(candidate_gates):
            prev_cx, prev_cy = prev_gate['center']
            if prev_cx < cx:
                dx = cx - prev_cx
                dy = abs(cy - prev_cy)
                distance_score = dx * 1.5 + dy
                candidates.append((distance_score, gate_outputs.get(prev_idx)))
        candidates.sort()
        for i in range(min(required_inputs, len(candidates))):
            assigned_inputs.append(candidates[i][1])
        while len(assigned_inputs) < required_inputs and input_idx < len(input_vars):
            assigned_inputs.append(input_vars[input_idx])
            input_idx += 1

    gate_inputs[idx] = assigned_inputs
    gate_outputs[idx] = output_labels[idx]

# === Map Boolean Expressions ===
output_expressions = {}
for idx, gate in enumerate(sorted_gates):
    cls_label = class_labels[gate['class_id']]
    inputs = gate_inputs.get(idx, [])
    output = gate_outputs.get(idx)
    if cls_label == "NOT" and len(inputs) == 1:
        expr = f"(NOT {inputs[0]})"
    elif len(inputs) == 2:
        expr = f"({inputs[0]} {cls_label} {inputs[1]})"
    else:
        expr = f"({cls_label} {' '.join(inputs)})"
    output_expressions[output] = expr

# === Resolve Final Output Expression ===
def resolve_expression(expr):
    tokens = expr.replace('(', '').replace(')', '').split()
    resolved = []
    for token in tokens:
        if token in output_expressions:
            resolved.append(f"({resolve_expression(output_expressions[token])})")
        else:
            resolved.append(token)
    return ' '.join(resolved)

# === Determine Final Output ===
rightmost_gate_idx = sorted_gates.index(max(sorted_gates, key=lambda g: g['center'][0]))
final_output_label = gate_outputs[rightmost_gate_idx]
final_expr = resolve_expression(output_expressions[final_output_label])

# === Annotate Image: Only Inputs and Final Output ===
for idx, gate in enumerate(sorted_gates):
    x1, y1, x2, y2 = gate['bbox']
    cx, cy = gate['center']

    # Draw bounding box and center for reference (optional)
    cv2.rectangle(annotated_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.circle(annotated_img, (cx, cy), 4, (255, 0, 0), -1)

    # Input annotations
    if idx in input_front_gates:
        inputs = gate_inputs.get(idx, [])
        cv2.putText(annotated_img, f"{','.join(inputs)}",
                    (max(x1 - 80, 5), y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

    # Output annotation
    if idx == rightmost_gate_idx:
        cv2.putText(annotated_img, "Y",
                    (min(x2 + 10, annotated_img.shape[1] - 60), y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 128, 255), 2)

# === Print Final Boolean Expression ===
print("===== Final Boolean Expression =====")
print(f"Y = {final_expr}")

# === Display Annotated Image ===
annotated_rgb = cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB)
plt.figure(figsize=(10, 10))
plt.imshow(annotated_rgb)
plt.axis('off')
plt.title("Logic Circuit: Inputs and Final Output Only")
plt.show()
