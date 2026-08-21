"""Deterministic scenario checks for Inverter.check_state semantics."""

from __future__ import annotations

import ast
from pathlib import Path


def load_extracted_inverter_class(repo_root: Path):
    target = repo_root / "InverterAutomation" / "inverter_dut.py"
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(target))

    selected = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Inverter":
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name in {
                    "_value_indicates_fault",
                    "check_state",
                }:
                    selected.append(member)
            break

    if len(selected) < 2:
        raise RuntimeError("Could not find required methods in Inverter class")

    class_node = ast.ClassDef(
        name="ExtractedInverter",
        bases=[],
        keywords=[],
        body=selected,
        decorator_list=[],
    )
    module = ast.Module(body=[class_node], type_ignores=[])
    ast.fix_missing_locations(module)

    namespace = {}
    exec(compile(module, filename=str(target), mode="exec"), namespace)
    return namespace["ExtractedInverter"]


def run_case(case_name, cls, payload, expected_state, expected_trips=None, expected_hw_trips=None):
    obj = cls()
    obj.tripsList = ["STALE_TRIP"]
    obj.hwTripsList = ["STALE_HW_TRIP"]
    obj.latest_payload_snapshot = lambda p=payload: p

    actual_state = obj.check_state()
    if actual_state != expected_state:
        return "{0}: expected_state={1} actual_state={2}".format(case_name, expected_state, actual_state)

    if expected_trips is not None and obj.tripsList != expected_trips:
        return "{0}: expected_trips={1} actual_trips={2}".format(case_name, expected_trips, obj.tripsList)

    if expected_hw_trips is not None and obj.hwTripsList != expected_hw_trips:
        return "{0}: expected_hw_trips={1} actual_hw_trips={2}".format(case_name, expected_hw_trips, obj.hwTripsList)

    return None


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    inverter_cls = load_extracted_inverter_class(repo_root)

    cases = [
        ("no_payload", {}, "NoData", ["STALE_TRIP"], ["STALE_HW_TRIP"]),
        ("no_trip_keys", {"control_status": True}, "NoData", ["STALE_TRIP"], ["STALE_HW_TRIP"]),
        ("empty_trip_lists", {"tripsList": [], "hwTripsList": []}, "Normal", [], []),
        ("trips_fault_list", {"tripsList": ["TRIP_A"], "hwTripsList": []}, "Fault", ["TRIP_A"], []),
        ("hw_fault_list", {"tripsList": [], "hwTripsList": ["HW_TRIP_A"]}, "Fault", [], ["HW_TRIP_A"]),
        ("encoded_empty_strings", {"tripsList": "[]", "hwTripsList": "null"}, "Normal", "[]", "null"),
        ("fallback_keys_normal", {"sup_trip": 0, "hw_trip": 0}, "Normal", ["STALE_TRIP"], ["STALE_HW_TRIP"]),
        ("fallback_keys_fault", {"sup_trip": 0, "hw_trip": 1}, "Fault", ["STALE_TRIP"], ["STALE_HW_TRIP"]),
        ("stale_cache_ignored", {"tripsList": [], "hwTripsList": []}, "Normal", [], []),
    ]

    failures = []
    for name, payload, expected_state, expected_trips, expected_hw_trips in cases:
        failure = run_case(name, inverter_cls, payload, expected_state, expected_trips, expected_hw_trips)
        if failure is not None:
            failures.append(failure)

    if failures:
        print("INVERTER_CHECK_STATE_FAIL")
        for failure in failures:
            print(failure)
        return 1

    print("INVERTER_CHECK_STATE_PASS")
    print("cases={0}".format(len(cases)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
