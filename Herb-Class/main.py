import os
import argparse
import sys

from herb_data import detect_structure_from_path_txt, collect_train_images, collect_infer_images, train_val_split
from train import TrainConfig, train_model
from infer import classify_images


def cmd_list(args):
    paths = detect_structure_from_path_txt(args.path_txt)
    by_class = collect_train_images(paths.train_root)
    infer_imgs = collect_infer_images(paths.infer_root)
    print(f"Project root: {paths.project_root}")
    print(f"Train root:   {paths.train_root}")
    print(f"Infer root:   {paths.infer_root}")
    print("\nTrain classes and counts:")
    for cls, items in by_class.items():
        print(f"  {cls}: {len(items)}")
    print(f"\nInfer images: {len(infer_imgs)}")


def cmd_train(args):
    paths = detect_structure_from_path_txt(args.path_txt)
    by_class = collect_train_images(paths.train_root)
    train_items, val_items, class_names = train_val_split(by_class, val_ratio=args.val_ratio)
    cfg = TrainConfig(
        img_size=args.img_size,
        batch_size=args.batch_size,
        epochs=args.epochs,
        lr=args.lr,
        model_name=args.model_name,
        freeze_backbone=not args.unfreeze,
        out_dir=args.out_dir,
    )
    best_ckpt = train_model(train_items, val_items, class_names, cfg)
    print(f"Best checkpoint saved to: {best_ckpt}")


def cmd_infer(args):
    paths = detect_structure_from_path_txt(args.path_txt)
    infer_imgs = collect_infer_images(paths.infer_root)
    if len(infer_imgs) == 0:
        print("No images found in infer directory.")
        return
    out_csv = classify_images(infer_imgs, args.checkpoint, out_csv=args.out_csv)
    print(f"Inference results saved to: {out_csv}")


def cmd_web(args):
    # Programmatically launch Streamlit app
    app_path = os.path.join(os.path.dirname(__file__), 'streamlit_app.py')
    if not os.path.isfile(app_path):
        print(f"Streamlit app not found: {app_path}")
        sys.exit(1)
    try:
        from streamlit.web import bootstrap
        bootstrap.run(app_path, '', [], {})
    except Exception:
        # fallback for older streamlit
        from streamlit.web.bootstrap import run
        run(app_path, '', [], {})


def build_parser():
    p = argparse.ArgumentParser(description='Herb Image Classification System')
    sub = p.add_subparsers(dest='cmd', required=True)

    sp = sub.add_parser('list', help='List dataset summary from path.txt')
    sp.add_argument('--path-txt', default='path.txt', help='Path to path.txt')
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser('train', help='Train lightweight classifier on CPU')
    sp.add_argument('--path-txt', default='path.txt', help='Path to path.txt')
    sp.add_argument('--img-size', type=int, default=224)
    sp.add_argument('--batch-size', type=int, default=32)
    sp.add_argument('--epochs', type=int, default=5)
    sp.add_argument('--lr', type=float, default=1e-3)
    sp.add_argument('--model-name', default='mobilenetv3_small_100', help='timm model name')
    sp.add_argument('--unfreeze', action='store_true', help='Unfreeze backbone for full fine-tuning')
    sp.add_argument('--val-ratio', type=float, default=0.1)
    sp.add_argument('--out-dir', default='models')
    sp.set_defaults(func=cmd_train)

    sp = sub.add_parser('infer', help='Run inference for images in infer folder')
    sp.add_argument('--path-txt', default='path.txt', help='Path to path.txt')
    sp.add_argument('--checkpoint', default=os.path.join('models', 'best.pth'))
    sp.add_argument('--out-csv', default='infer_results.csv')
    sp.set_defaults(func=cmd_infer)

    sp = sub.add_parser('web', help='Launch Streamlit web UI')
    sp.set_defaults(func=cmd_web)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()