import os
from dataclasses import dataclass
from typing import List, Tuple

import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import timm
from torchvision import transforms
from tqdm import tqdm


class ImageClassDataset(Dataset):
    def __init__(self, items: List[Tuple[str, int]], img_size: int = 224):
        self.items = items
        self.tf = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        path, label = self.items[idx]
        img = Image.open(path).convert('RGB')
        return self.tf(img), torch.tensor(label, dtype=torch.long)


@dataclass
class TrainConfig:
    img_size: int = 224
    batch_size: int = 32
    epochs: int = 5
    lr: float = 1e-3
    model_name: str = 'mobilenetv3_small_100'
    freeze_backbone: bool = True
    out_dir: str = 'models'


def build_model(num_classes: int, cfg: TrainConfig) -> nn.Module:
    model = timm.create_model(cfg.model_name, pretrained=True, num_classes=num_classes)
    if cfg.freeze_backbone:
        for name, p in model.named_parameters():
            # keep classifier head trainable
            if 'classifier' in name or 'fc' in name:
                p.requires_grad = True
            else:
                p.requires_grad = False
    return model


def train_model(train_items: List[Tuple[str, int]], val_items: List[Tuple[str, int]], class_names: List[str], cfg: TrainConfig) -> str:
    os.makedirs(cfg.out_dir, exist_ok=True)
    device = torch.device('cpu')
    torch.set_num_threads(max(1, os.cpu_count() or 1))

    model = build_model(len(class_names), cfg)
    model.to(device)

    train_ds = ImageClassDataset(train_items, img_size=cfg.img_size)
    val_ds = ImageClassDataset(val_items, img_size=cfg.img_size)
    train_loader = DataLoader(train_ds, batch_size=cfg.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=cfg.batch_size, shuffle=False, num_workers=0)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=cfg.lr)

    best_val_acc = 0.0
    best_path = os.path.join(cfg.out_dir, 'best.pth')

    for epoch in range(cfg.epochs):
        model.train()
        total, correct, loss_sum = 0, 0, 0.0
        pbar = tqdm(train_loader, desc=f'Epoch {epoch+1}/{cfg.epochs} [train]')
        for x, y in pbar:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            loss_sum += loss.item() * y.size(0)
            preds = logits.argmax(dim=1)
            correct += (preds == y).sum().item()
            total += y.size(0)
            pbar.set_postfix(loss=f"{loss_sum/total:.4f}", acc=f"{correct/total:.3f}")

        # validation
        model.eval()
        total, correct = 0, 0
        with torch.no_grad():
            for x, y in tqdm(val_loader, desc=f'Epoch {epoch+1}/{cfg.epochs} [val]'):
                x, y = x.to(device), y.to(device)
                logits = model(x)
                preds = logits.argmax(dim=1)
                correct += (preds == y).sum().item()
                total += y.size(0)
        val_acc = correct / max(1, total)

        # save best
        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            torch.save({'model': model.state_dict(), 'class_names': class_names, 'cfg': cfg.__dict__}, best_path)

    # persist class names as text
    with open(os.path.join(cfg.out_dir, 'classes.txt'), 'w', encoding='utf-8') as f:
        for name in class_names:
            f.write(name + '\n')

    return best_path