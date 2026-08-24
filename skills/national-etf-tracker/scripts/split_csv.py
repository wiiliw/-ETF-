#!/usr/bin/env python3
"""Split large CSVs into GitHub-friendly chunks and optionally merge them back."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd


def split_csv(source: Path, output_dir: Path, rows: int) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = source.stem
    paths: list[Path] = []
    for index, frame in enumerate(pd.read_csv(source, chunksize=rows, dtype={"code": str}), 1):
        target = output_dir / f"{stem}.part-{index:03d}.csv"
        frame.to_csv(target, index=False, encoding="utf-8-sig")
        paths.append(target)
    return paths


def merge_csv(parts: list[Path], target: Path) -> None:
    if not parts:
        raise SystemExit("没有找到分片文件")
    first = True
    target.parent.mkdir(parents=True, exist_ok=True)
    for part in parts:
        frame = pd.read_csv(part, dtype={"code": str})
        frame.to_csv(target, mode="w" if first else "a", header=first, index=False, encoding="utf-8-sig")
        first = False


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    s = sub.add_parser("split")
    s.add_argument("--input", required=True)
    s.add_argument("--output-dir", required=True)
    s.add_argument("--rows", type=int, default=100_000)
    m = sub.add_parser("merge")
    m.add_argument("--parts-glob", required=True)
    m.add_argument("--output", required=True)
    args = ap.parse_args()
    if args.command == "split":
        paths = split_csv(Path(args.input), Path(args.output_dir), args.rows)
        print(f"split {args.input} into {len(paths)} parts")
        for path in paths:
            print(f"{path} {path.stat().st_size / 1024 / 1024:.2f} MB")
    else:
        parts = sorted(Path().glob(args.parts_glob))
        merge_csv(parts, Path(args.output))
        print(f"merged {len(parts)} parts into {args.output}")


if __name__ == "__main__":
    main()
