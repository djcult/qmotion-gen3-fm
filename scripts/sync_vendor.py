"""Keep HACS runtime copies identical to the single-source Python library."""
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "qmotion_gen3_fm"
TARGET = ROOT / "custom_components" / "qmotion_gen3_fm" / "vendor"
FILES = ("gateway.py", "protocol.py")


def main():
    check = "--check" in sys.argv
    for filename in FILES:
        source = SOURCE / filename
        target = TARGET / filename
        if check:
            if target.read_bytes() != source.read_bytes():
                raise SystemExit(f"Out of sync: {target}; run python scripts/sync_vendor.py")
        else:
            shutil.copyfile(source, target)
            print(f"Updated {target.relative_to(ROOT)}")
    if check:
        print("Bundled protocol sources are in sync.")


if __name__ == "__main__":
    main()
