from __future__ import annotations

import argparse
from pathlib import Path


def _parse_rule(raw: str) -> tuple[Path, int]:
    if "<=" not in raw:
        raise argparse.ArgumentTypeError(
            f"invalid rule {raw!r}; expected format: path<=max_lines"
        )
    raw_path, raw_limit = raw.split("<=", 1)
    path = Path(raw_path.strip())
    if not str(path):
        raise argparse.ArgumentTypeError("file-size rule path cannot be empty")
    try:
        limit = int(raw_limit.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid max line count in rule {raw!r}"
        ) from exc
    if limit <= 0:
        raise argparse.ArgumentTypeError("max line count must be positive")
    return path, limit


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail when tracked source files exceed configured line budgets."
    )
    parser.add_argument(
        "--rule",
        action="append",
        required=True,
        type=_parse_rule,
        help="Line budget rule in the form path<=max_lines.",
    )
    args = parser.parse_args()

    violations: list[str] = []
    for path, limit in args.rule:
        if not path.exists():
            violations.append(f"{path}: missing file for <= {limit} line budget")
            continue
        if not path.is_file():
            violations.append(f"{path}: not a file for <= {limit} line budget")
            continue
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > limit:
            violations.append(f"{path}: {line_count} lines > {limit}")

    if violations:
        print("File-size budget failed:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("File-size budget passed:")
    for path, limit in args.rule:
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        print(f"- {path}: {line_count} lines <= {limit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
