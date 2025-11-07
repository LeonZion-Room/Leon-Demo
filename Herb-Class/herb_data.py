import os
from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class DatasetPaths:
    project_root: str
    path_txt: str
    train_root: str
    infer_root: str


def detect_structure_from_path_txt(path_txt: str) -> DatasetPaths:
    """Parse path.txt to locate project root, train and infer folders.

    We only read necessary parts: paths containing 'Chinese Medicine/train' and 'Chinese Medicine/infer'.
    """
    if not os.path.isfile(path_txt):
        raise FileNotFoundError(f"path.txt not found: {path_txt}")

    train_root = None
    infer_root = None
    project_root = os.path.dirname(path_txt)

    with open(path_txt, 'r', encoding='utf-8') as f:
        for line in f:
            p = line.strip()
            if not p:
                continue
            # Normalize separators
            p_norm = p.replace('/', os.sep).replace('\\', os.sep)
            if 'Chinese Medicine' + os.sep + 'train' in p_norm:
                # capture the root up to 'train'
                idx = p_norm.index('Chinese Medicine' + os.sep + 'train')
                train_root = p_norm[: idx + len('Chinese Medicine' + os.sep + 'train')]
            elif 'Chinese Medicine' + os.sep + 'infer' in p_norm:
                idx = p_norm.index('Chinese Medicine' + os.sep + 'infer')
                infer_root = p_norm[: idx + len('Chinese Medicine' + os.sep + 'infer')]

    # Fallback to typical layout if not found via path.txt
    if train_root is None:
        maybe = os.path.join(project_root, 'Chinese Medicine', 'train')
        if os.path.isdir(maybe):
            train_root = maybe
    if infer_root is None:
        maybe = os.path.join(project_root, 'Chinese Medicine', 'infer')
        if os.path.isdir(maybe):
            infer_root = maybe

    if train_root is None or infer_root is None:
        raise RuntimeError('Failed to locate train/infer directories from path.txt or default layout.')

    return DatasetPaths(
        project_root=project_root,
        path_txt=path_txt,
        train_root=train_root,
        infer_root=infer_root,
    )


def list_train_classes(train_root: str) -> List[str]:
    """List class folder names under train_root."""
    classes = []
    for name in os.listdir(train_root):
        p = os.path.join(train_root, name)
        if os.path.isdir(p):
            classes.append(name)
    classes.sort()
    return classes


def collect_train_images(train_root: str) -> Dict[str, List[str]]:
    """Collect image file paths grouped by class folder."""
    result: Dict[str, List[str]] = {}
    for cls in list_train_classes(train_root):
        cls_dir = os.path.join(train_root, cls)
        imgs = []
        for fname in os.listdir(cls_dir):
            if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp')):
                imgs.append(os.path.join(cls_dir, fname))
        imgs.sort()
        result[cls] = imgs
    return result


def collect_infer_images(infer_root: str) -> List[str]:
    imgs: List[str] = []
    for fname in os.listdir(infer_root):
        if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp')):
            imgs.append(os.path.join(infer_root, fname))
    imgs.sort()
    return imgs


def train_val_split(paths_by_class: Dict[str, List[str]], val_ratio: float = 0.1) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]], List[str]]:
    """Split into train/val lists of (path, class_idx) and return class_names."""
    class_names = sorted(paths_by_class.keys())
    train_items: List[Tuple[str, int]] = []
    val_items: List[Tuple[str, int]] = []
    for idx, cls in enumerate(class_names):
        imgs = paths_by_class[cls]
        n = len(imgs)
        if n == 0:
            continue
        split = max(1, int(n * val_ratio))
        val_items += [(p, idx) for p in imgs[:split]]
        train_items += [(p, idx) for p in imgs[split:]]
    return train_items, val_items, class_names