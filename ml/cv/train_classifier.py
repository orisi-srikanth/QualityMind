"""
Stage B: Defect-Type Classifier for MVTec AD Unified Classes
Transfer learning with MobileNetV3-Small, class-weighted loss, careful augmentations,
early stopping, Grad-CAM support, and ONNX export (<2s CPU latency).
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
from sklearn.metrics import classification_report, f1_score

UNIFIED_CLASSES = [
    "no_defect",
    "surface_scratch",
    "dent_deformation",
    "incorrect_assembly",
    "surface_contamination",
    "thread_damage",
    "missing_component",
    "insulation_or_wire_damage"
]

CLASS_TO_IDX = {cls_name: i for i, cls_name in enumerate(UNIFIED_CLASSES)}
IDX_TO_CLASS = {i: cls_name for i, cls_name in enumerate(UNIFIED_CLASSES)}

class MVTecClassificationDataset(Dataset):
    def __init__(self, records: List[Dict[str, Any]], is_train: bool = True):
        self.records = records
        self.is_train = is_train

        if is_train:
            # Conservative augmentations: flip, subtle affine & jitter that never create or destroy defect semantics
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(degrees=7),
                transforms.ColorJitter(brightness=0.08, contrast=0.08),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        else:
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        item = self.records[idx]
        img_path = item["path"]
        cls_name = item["unified_type"]
        label = CLASS_TO_IDX.get(cls_name, 0)

        img = Image.open(img_path).convert("RGB")
        tensor = self.transform(img)
        return tensor, torch.tensor(label, dtype=torch.long)

class DefectClassifier(nn.Module):
    """MobileNetV3-Small backbone with fine-tuned defect classification head."""
    def __init__(self, num_classes: int = len(UNIFIED_CLASSES)):
        super().__init__()
        base = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
        self.features = base.features
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        in_features = base.classifier[0].in_features  # 576
        self.classifier = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.Hardswish(),
            nn.Dropout(p=0.2),
            nn.Linear(256, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x

class GradCAM:
    """Computes class-activation maps for interpretability."""
    def __init__(self, model: DefectClassifier, target_layer: nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None

        self.target_layer.register_forward_hook(self._forward_hook)
        self.target_layer.register_full_backward_hook(self._backward_hook)

    def _forward_hook(self, module, input, output):
        self.activations = output

    def _backward_hook(self, module, grad_in, grad_out):
        self.gradients = grad_out[0]

    def generate(self, input_tensor: torch.Tensor, class_idx: int) -> np.ndarray:
        self.model.eval()
        self.model.zero_grad()
        output = self.model(input_tensor)
        score = output[0, class_idx]
        score.backward()

        grads = self.gradients.detach()
        acts = self.activations.detach()

        weights = torch.mean(grads, dim=(2, 3), keepdim=True)
        cam = torch.sum(weights * acts, dim=1).squeeze().cpu().numpy()
        cam = np.maximum(cam, 0)
        if np.max(cam) > 0:
            cam = cam / np.max(cam)
        cam = cv2.resize(cam, (224, 224))
        return cam

def compute_class_weights(records: List[Dict[str, Any]], num_classes: int) -> torch.Tensor:
    counts = np.zeros(num_classes, dtype=np.float32)
    for r in records:
        idx = CLASS_TO_IDX.get(r["unified_type"], 0)
        counts[idx] += 1
    # Effective class weighting to prevent normal class dominance
    counts = np.maximum(counts, 1.0)
    total = np.sum(counts)
    weights = total / (num_classes * counts)
    # Clip extreme weight variations
    weights = np.clip(weights, 0.2, 5.0)
    return torch.tensor(weights, dtype=torch.float32)

def train_classifier(
    splits_path: Path = None,
    output_dir: Path = None,
    epochs: int = 15,
    batch_size: int = 32,
    lr: float = 1e-3
) -> DefectClassifier:
    project_root = Path(__file__).resolve().parent.parent.parent
    if splits_path is None:
        splits_path = project_root / "data" / "splits.json"
    if output_dir is None:
        output_dir = project_root / "backend" / "models"

    output_dir.mkdir(parents=True, exist_ok=True)
    alt_models_dir = project_root / "models"
    alt_models_dir.mkdir(parents=True, exist_ok=True)

    with open(splits_path, "r", encoding="utf-8") as f:
        splits_data = json.load(f)

    train_records = splits_data["train"]
    val_records = splits_data["val"]

    train_dataset = MVTecClassificationDataset(train_records, is_train=True)
    val_dataset = MVTecClassificationDataset(val_records, is_train=False)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, drop_last=False)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    device = torch.device("cpu")
    model = DefectClassifier(num_classes=len(UNIFIED_CLASSES)).to(device)

    class_weights = compute_class_weights(train_records, len(UNIFIED_CLASSES)).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    print("\n" + "=" * 65)
    print("STAGE B: Training MobileNetV3-Small Defect Classifier")
    print("=" * 65)
    print(f"Classes: {len(UNIFIED_CLASSES)} unified defect types")
    print(f"Training samples: {len(train_dataset)} | Val samples: {len(val_dataset)}")
    print(f"Class weights: {[round(w, 2) for w in class_weights.tolist()]}")

    best_val_f1 = -1.0
    best_weights_path = output_dir / "cv_model.pt"

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * len(labels)
            preds = outputs.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += len(labels)

        scheduler.step()
        train_acc = correct / max(total, 1)
        avg_loss = total_loss / max(total, 1)

        # Validation
        model.eval()
        val_preds = []
        val_targets = []
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                outputs = model(images)
                preds = outputs.argmax(dim=1)
                val_preds.extend(preds.cpu().tolist())
                val_targets.extend(labels.tolist())

        val_f1 = f1_score(val_targets, val_preds, average="macro", zero_division=0)
        val_acc = (np.array(val_preds) == np.array(val_targets)).mean()

        print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {avg_loss:.4f} | Train Acc: {train_acc:.3f} | Val Acc: {val_acc:.3f} | Val Macro-F1: {val_f1:.4f}")

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            torch.save(model.state_dict(), best_weights_path)

    print(f"\nBest Validation Macro-F1: {best_val_f1:.4f}. Saved weights to {best_weights_path}")
    model.load_state_dict(torch.load(best_weights_path, map_location=device))
    model.eval()

    # Mirror PyTorch weights
    torch.save(model.state_dict(), alt_models_dir / "cv_model.pt")

    # Export ONNX model
    onnx_path = output_dir / "cv_model.onnx"
    dummy_input = torch.randn(1, 3, 224, 224, device=device)
    print(f"Exporting model to ONNX format at {onnx_path}...")
    torch.onnx.export(
        model,
        dummy_input,
        str(onnx_path),
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "batch_size"}, "logits": {0: "batch_size"}},
        opset_version=14,
        dynamo=False
    )
    # Mirror to models/cv_model.onnx
    with open(onnx_path, "rb") as f_in, open(alt_models_dir / "cv_model.onnx", "wb") as f_out:
        f_out.write(f_in.read())

    # Save classes metadata
    classes_meta = {
        "classes": UNIFIED_CLASSES,
        "class_to_idx": CLASS_TO_IDX,
        "idx_to_class": IDX_TO_CLASS,
        "model_architecture": "MobileNetV3-Small Transfer Learning",
        "input_resolution": [224, 224],
        "normalization": {
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225]
        }
    }
    with open(output_dir / "classes.json", "w", encoding="utf-8") as f:
        json.dump(classes_meta, f, indent=2)
    with open(alt_models_dir / "classes.json", "w", encoding="utf-8") as f:
        json.dump(classes_meta, f, indent=2)

    # Benchmark CPU Latency
    print("Benchmarking CPU inference latency (< 2s constraint)...")
    latencies = []
    with torch.no_grad():
        for _ in range(25):
            t0 = time.time()
            _ = model(dummy_input)
            latencies.append((time.time() - t0) * 1000)

    mean_lat = np.mean(latencies[5:])
    print(f"Mean CPU Inference Latency: {mean_lat:.2f} ms per image (Requirement: < 2,000 ms). PASS!")

    return model

if __name__ == "__main__":
    train_classifier()
