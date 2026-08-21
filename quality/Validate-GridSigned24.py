"""Deterministic vector checks for GridSimulator._decode_signed_24."""

from __future__ import annotations

import ast
from pathlib import Path


def load_decoder(repo_root: Path):
    target = repo_root / "gridSimulator" / "grid_simulator.py"
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(target))

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "GridSimulator":
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == "_decode_signed_24":
                    member.decorator_list = []
                    module = ast.Module(body=[member], type_ignores=[])
                    ast.fix_missing_locations(module)
                    namespace = {}
                    exec(compile(module, filename=str(target), mode="exec"), namespace)
                    return namespace["_decode_signed_24"]

    raise RuntimeError("Could not find GridSimulator._decode_signed_24")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    decode = load_decoder(repo_root)

    vectors = [
        (bytes.fromhex("000000"), 0),
        (bytes.fromhex("000001"), 1),
        (bytes.fromhex("0000FF"), 255),
        (bytes.fromhex("7FFFFF"), 8388607),
        (bytes.fromhex("800000"), 0),
        (bytes.fromhex("800001"), -1),
        # Hardware-observed negative active-power frames from bench validation.
        (bytes.fromhex("800A9F"), -2719),
        (bytes.fromhex("800AA0"), -2720),
        (bytes.fromhex("FFFFFF"), -8388607),
    ]

    failures = []
    for raw, expected in vectors:
        actual = decode(raw)
        if actual != expected:
            failures.append((raw.hex().upper(), expected, actual))

    if failures:
        print("GRID_SIGNED24_FAIL")
        for item in failures:
            print("vector={0} expected={1} actual={2}".format(*item))
        return 1

    print("GRID_SIGNED24_PASS")
    print("vectors={0}".format(len(vectors)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
