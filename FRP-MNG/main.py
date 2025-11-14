import argparse
from pathlib import Path
import sys
from frp_manager.config import ensure_base, set_binaries, save_profile_from_file, list_profiles, generate_ini
from frp_manager.process import start_profile, stop_profile, profile_status

def _base_dir() -> Path:
    return Path.cwd() / ".frp-manager"

def cmd_init(args: argparse.Namespace) -> int:
    ensure_base(_base_dir())
    return 0

def cmd_configure(args: argparse.Namespace) -> int:
    ensure_base(_base_dir())
    set_binaries(_base_dir(), client=args.client, server=args.server)
    return 0

def cmd_create(args: argparse.Namespace) -> int:
    ensure_base(_base_dir())
    save_profile_from_file(_base_dir(), args.type, args.name, Path(args.file))
    return 0

def cmd_generate_ini(args: argparse.Namespace) -> int:
    ensure_base(_base_dir())
    p = generate_ini(_base_dir(), args.type, args.name)
    print(str(p))
    return 0

def cmd_list(args: argparse.Namespace) -> int:
    ensure_base(_base_dir())
    items = list_profiles(_base_dir(), args.type)
    for x in items:
        print(x)
    return 0

def cmd_start(args: argparse.Namespace) -> int:
    ensure_base(_base_dir())
    pid = start_profile(_base_dir(), args.type, args.name)
    print(pid)
    return 0

def cmd_stop(args: argparse.Namespace) -> int:
    ensure_base(_base_dir())
    stop_profile(_base_dir(), args.type, args.name)
    return 0

def cmd_status(args: argparse.Namespace) -> int:
    ensure_base(_base_dir())
    s = profile_status(_base_dir(), args.type, args.name)
    print("running" if s else "stopped")
    return 0

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="frp-manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("configure")
    sp.add_argument("--client", required=False)
    sp.add_argument("--server", required=False)
    sp.set_defaults(func=cmd_configure)

    sp = sub.add_parser("create")
    sp.add_argument("--type", choices=["client", "server"], required=True)
    sp.add_argument("--name", required=True)
    sp.add_argument("--file", required=True)
    sp.set_defaults(func=cmd_create)

    sp = sub.add_parser("generate-ini")
    sp.add_argument("--type", choices=["client", "server"], required=True)
    sp.add_argument("--name", required=True)
    sp.set_defaults(func=cmd_generate_ini)

    sp = sub.add_parser("list")
    sp.add_argument("--type", choices=["client", "server"], required=True)
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("start")
    sp.add_argument("--type", choices=["client", "server"], required=True)
    sp.add_argument("--name", required=True)
    sp.set_defaults(func=cmd_start)

    sp = sub.add_parser("stop")
    sp.add_argument("--type", choices=["client", "server"], required=True)
    sp.add_argument("--name", required=True)
    sp.set_defaults(func=cmd_stop)

    sp = sub.add_parser("status")
    sp.add_argument("--type", choices=["client", "server"], required=True)
    sp.add_argument("--name", required=True)
    sp.set_defaults(func=cmd_status)

    return p

def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))