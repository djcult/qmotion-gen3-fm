"""Standalone administration CLI. Destructive operations are opt-in."""
import argparse
from .gateway import Gateway
from .management import (
    ERASE_PACKET, create_group_packet, delete_group_packet, next_channel, parse_mac
)

def choose(groups, name):
    matches = [g for g in groups if g.name == name]
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one group named {name!r}, found {len(matches)}")
    return matches[0]

def confirm(token, message):
    if input(f"{message}\nType {token} to continue: ").strip() != token:
        raise SystemExit("Cancelled; no command sent")

def run_pairing(gateway, group, ask=input, output=print, dry_run=True):
    """Guide an operator through pairing without modifying unrelated groups.

    The motor's physical jog is the only confirmation of successful RF reception.
    """
    from .protocol import prepare_pairing, complete_pairing

    prepare = prepare_pairing(group.channel)
    finish = complete_pairing(group.channel, group.page)
    output(f"\nPairing group {group.name!r}" + (" [DRY RUN — NO TRANSMISSION]" if dry_run else ""))
    output(f"  Channel: {group.channel}")
    output(f"  Page address: {group.page.hex(' ')}")
    output(f"  Preparation: {prepare.hex(' ')}")
    output(f"  Completion:  {finish.hex(' ')}")
    output("This procedure modifies the motor's learned controller assignments.")
    output("Keep the original handheld remote available; do not reset the blind.")
    ready_prompt = "Simulate blind fully raised. Type READY: " if dry_run else "Raise the blind FULLY using its remote. Type READY when positioned: "
    if ask(ready_prompt).strip() != "READY":
        output("Cancelled: no RF command sent.")
        return False

    if ask("Send Special Learn preparation? Type SEND: ").strip() != "SEND":
        output("Cancelled: no RF command sent.")
        return False
    if not dry_run:
        gateway.prepare_pairing(group.channel)
    output("Preparation " + ("simulated (NOT transmitted)." if dry_run else "transmitted. Watch for the blind to lower toward its learn position."))
    if dry_run:
        output("SIMULATION: no motor movement or physical tug required.")
        jog_prompt = "Simulate a motor jog. Type JOG to proceed: "
    else:
        output("Once movement stops, gently tug the accessible blind cord.")
        output("The motor should give a short JOG confirming selection.")
        jog_prompt = "Did the blind JOG after your tug? Type JOG to proceed: "
    if ask(jog_prompt).strip() != "JOG":
        output("Stopped: pairing completion was NOT sent. If learning times out, restart pairing.")
        return False

    if ask(f"Complete pairing to {group.name!r} (page {group.page.hex(' ')})? Type PAIR: ").strip() != "PAIR":
        output("Stopped: pairing completion was NOT sent.")
        return False
    if not dry_run:
        gateway.complete_pairing(group)
    output("Completion " + ("simulated (NOT transmitted)." if dry_run else "command transmitted."))
    if not dry_run:
        output("Watch for another jog and the blind returning to its upper limit.")
    if not dry_run:
        output("Verify open/close separately, and verify the original remote still works.")
    output("No motor acknowledgement is available over this one-way RF protocol.")
    return True

def main():
    parser = argparse.ArgumentParser(description="QMotion Gen 3 FM QSync administration")
    parser.add_argument("--host", required=True, help="QSync gateway IP")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("groups", help="List gateway group records")
    position = sub.add_parser("position", help="Set position (0=open; 100=closed)")
    position.add_argument("group")
    position.add_argument("percent", type=int)
    pair = sub.add_parser("pair", help="Guided physical-tug pairing")
    pair.add_argument("group")
    pair.add_argument("--send", action="store_true", help="Transmit real pairing commands after confirmation; default is dry-run")
    create = sub.add_parser("create", help="Create a group (experimental)")
    create.add_argument("name")
    create.add_argument("--mac", help="Gateway MAC; required if no existing group provides it")
    create.add_argument("--channel", type=int, help="Override next free channel")
    create.add_argument("--send", action="store_true", help="Actually transmit after confirmation")
    delete = sub.add_parser("delete", help="Delete gateway group record; does NOT unpair motor")
    delete.add_argument("group")
    delete.add_argument("--send", action="store_true")
    erase = sub.add_parser("erase", help="Erase all gateway groups and scenes; motor pairing persists")
    erase.add_argument("--send", action="store_true")
    args = parser.parse_args()
    gateway = Gateway(args.host)
    groups = gateway.list_groups()
    if args.command == "groups":
        if not groups:
            print("No groups configured")
        for g in groups:
            print(f"{g.name}: channel={g.channel} page={g.page.hex(' ')}")
        return
    if args.command == "create":
        if any(g.name == args.name for g in groups):
            raise SystemExit("Name already exists")
        used = {g.channel for g in groups}
        channel = args.channel if args.channel is not None else next_channel(used)
        if channel in used:
            raise SystemExit(f"Channel {channel} already allocated")
        if args.mac:
            mac = parse_mac(args.mac)
            if groups and mac != groups[0].raw[9:15]:
                raise SystemExit("Supplied MAC differs from existing gateway group records")
        elif groups:
            mac = groups[0].raw[9:15]
            if any(g.raw[9:15] != mac for g in groups):
                raise SystemExit("Inconsistent MAC in gateway groups; specify --mac after investigation")
        else:
            raise SystemExit("Empty gateway: supply its verified MAC using --mac XX:XX:XX:XX:XX:XX")
        packet = create_group_packet(args.name, mac, channel)
        print(f"CREATE {args.name!r}, channel={channel}, MAC={mac.hex(':')}; bytes={packet.hex(' ')}")
    elif args.command == "delete":
        group = choose(groups, args.group)
        packet = delete_group_packet(group.page)
        print(f"DELETE {group.name!r}, channel={group.channel}, page={group.page.hex(' ')}; bytes={packet.hex(' ')}")
    elif args.command == "erase":
        packet = ERASE_PACKET
        print(f"ERASE ALL {len(groups)} gateway groups/scenes; bytes={packet.hex(' ')}")
    elif args.command == "position":
        group = choose(groups, args.group)
        if not 0 <= args.percent <= 100:
            parser.error("percent must be 0..100")
        confirm("SEND", f"Move {group.name!r} to {args.percent}%?")
        gateway.set_position(group.channel, args.percent)
        print("Command transmitted; motor delivery not acknowledged")
        return
    elif args.command == "pair":
        group = choose(groups, args.group)
        run_pairing(gateway, group, dry_run=not args.send)
        return
    if not args.send:
        print("DRY RUN: nothing transmitted. Add --send to permit transmission.")
        return
    token = f"ERASE {args.host}" if args.command == "erase" else f"{args.command.upper()} {args.group if args.command == 'delete' else args.name}"
    confirm(token, f"EXPERIMENTAL {args.command.upper()} operation. Verify target and backup configuration first.")
    response = gateway.exchange(packet)
    print(f"Sent; response={response.hex(' ') if response else '(none)'}")
    print("Re-read group list to verify actual result. No ACK does not prove success.")

if __name__ == "__main__":
    main()
