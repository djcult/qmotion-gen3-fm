"""Standalone gateway admin CLI. No erase/delete commands in initial release."""
import argparse
from .gateway import Gateway

def select_group(gateway: Gateway, name: str):
    matches = [g for g in gateway.list_groups() if g.name == name]
    if len(matches) != 1:
        raise SystemExit(f"Expected one group named {name!r}, found {len(matches)}")
    return matches[0]

def confirm(message: str) -> None:
    if input(f"{message}\nType SEND to continue: ").strip() != "SEND":
        raise SystemExit("Cancelled; no command sent")

def main() -> None:
    parser = argparse.ArgumentParser(description="QMotion Gen 3 FM QSync administration")
    parser.add_argument("--host", required=True, help="QSync gateway IP address")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("groups", help="Read gateway group records")
    move_cmd = sub.add_parser("position", help="Send position, 0=open 100=closed")
    move_cmd.add_argument("group")
    move_cmd.add_argument("percent", type=int)
    pair_cmd = sub.add_parser("pair", help="Guided Special Learn pairing")
    pair_cmd.add_argument("group")
    args = parser.parse_args()
    gateway = Gateway(args.host)
    if args.command == "groups":
        groups = gateway.list_groups()
        if not groups:
            print("No groups configured")
        for group in groups:
            print(f"{group.name}: channel={group.channel} page={group.page.hex(' ')}")
    elif args.command == "position":
        group = select_group(gateway, args.group)
        if not 0 <= args.percent <= 100:
            parser.error("percent must be 0..100")
        confirm(f"Move {group.name!r} on channel {group.channel} to {args.percent}%?")
        gateway.set_position(group.channel, args.percent)
        print("Command transmitted (RF delivery is not acknowledged)")
    elif args.command == "pair":
        group = select_group(gateway, args.group)
        print(f"Pairing {group.name!r}: channel={group.channel}, page={group.page.hex(' ')}")
        print("Raise the blind fully using its existing remote.")
        confirm("Ready to send Special Learn preparation? Blind may move.")
        gateway.prepare_pairing(group.channel)
        print("Wait for blind movement to stop, then gently tug its accessible cord.")
        if input("Did the motor JOG after tugging? Type JOG to confirm: ").strip() != "JOG":
            raise SystemExit("Pairing completion not sent.")
        confirm("Send final pairing packet? This may change the motor's learned controllers.")
        gateway.complete_pairing(group)
        print("Completion transmitted. Verify movement and original remote manually.")

if __name__ == "__main__":
    main()
