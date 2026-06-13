#!/usr/bin/env python3
"""Assert the built wheel ships ONLY the MIT software license (audit re-review P3-11).

Locks the round-two licensing fix in CI: the wheel under dist/ must declare
'License: MIT' and contain exactly one license file, LICENSE-MIT, in its
dist-info/licenses/. Exits non-zero otherwise.
"""
import glob
import sys
import zipfile


def main() -> int:
    whls = sorted(glob.glob("dist/*.whl"))
    if not whls:
        print("no wheel found under dist/ (build it first)")
        return 1
    z = zipfile.ZipFile(whls[-1])
    names = z.namelist()
    lics = [n for n in names if ".dist-info/licenses/" in n]
    meta = z.read(next(n for n in names if n.endswith(".dist-info/METADATA"))).decode()
    errs = []
    if not (len(lics) == 1 and lics[0].endswith("LICENSE-MIT")):
        errs.append(f"expected exactly dist-info/licenses/LICENSE-MIT, got {lics}")
    if not any(line.strip() == "License: MIT" for line in meta.splitlines()):
        errs.append("wheel METADATA does not declare 'License: MIT'")
    if errs:
        for e in errs:
            print("WHEEL LICENSE ERROR:", e)
        return 1
    print(f"wheel license OK: only {lics[0]}; METADATA declares License: MIT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
