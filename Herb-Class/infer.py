import os
import csv
from typing import List

import torch
from PIL import Image
from torchvision import transforms
import timm


def load_model(checkpoint_path: str):
    ckpt = torch.load(checkpoint_path, map_location='cpu')
    class_names = ckpt.get('class_names')
    cfg = ckpt.get('cfg', {})
    model_name = cfg.get('model_name', 'mobilenetv3_small_100')
    num_classes = len(class_names)
    model = timm.create_model(model_name, pretrained=False, num_classes=num_classes)
    model.load_state_dict(ckpt['model'])
    model.eval()
    return model, class_names, cfg


def make_transform(img_size: int = 224):
    return transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def classify_images(image_paths: List[str], checkpoint_path: str, out_csv: str = 'infer_results.csv') -> str:
    if not os.path.isfile(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    model, class_names, cfg = load_model(checkpoint_path)
    tf = make_transform(img_size=int(cfg.get('img_size', 224)))
    device = torch.device('cpu')

    rows = []
    for p in image_paths:
        img = Image.open(p).convert('RGB')
        x = tf(img).unsqueeze(0).to(device)
        with torch.no_grad():
            logits = model(x)
            prob = torch.softmax(logits, dim=1)
            pred = prob.argmax(dim=1).item()
            conf = prob[0, pred].item()
            rows.append({'path': p, 'pred_class': class_names[pred], 'confidence': f"{conf:.4f}"})

    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['path', 'pred_class', 'confidence'])
        writer.writeheader()
        writer.writerows(rows)

    return out_csv