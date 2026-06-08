#!/usr/bin/env python3
"""
In-place re-encoder for the existing ``data/`` tree.

Walks every ``*.parquet`` under ``data/`` and rewrites it using the same
compact encoding that ``download_data.py`` uses for fresh downloads:

* float64 -> float32 downcast
* ``zstd`` level 5 compression
* microsecond timestamp resolution
* 8 MiB data pages (better brotli ratio on minute bars)

This avoids re-downloading from RQData/akshare (saves time and quota) while
still reclaiming ~30% of the on-disk footprint before ``git push``.

Idempotent: running it a second time is a no-op (sizes barely change).
Dry-run by default; pass ``--apply`` to actually rewrite files.
"""
import os
import sys
import time
import shutil
import tempfile
import argparse
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_DIR = os.path.join(_SCRIPT_DIR, 'data')
COMPRESSION = 'zstd'
COMPRESSION_LEVEL = 5


def _downcast_floats(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    for col in df.columns:
        if df[col].dtype == 'float64':
            df[col] = df[col].astype('float32')
    return df


def rewrite_one(path: str) -> tuple[int, int]:
    """Rewrite a single parquet file. Returns (old_bytes, new_bytes)."""
    old_size = os.path.getsize(path)
    df = pd.read_parquet(path)
    if df.empty:
        # Header-only files: rewrite once with plain pyarrow to normalise layout.
        pd.DataFrame().to_parquet(path, engine='pyarrow')
        return old_size, os.path.getsize(path)

    _downcast_floats(df)
    table = pa.Table.from_pandas(df, preserve_index=True)

    # Write atomically: temp file in same dir, then os.replace. Avoids leaving
    # half-written files if the process is killed mid-write.
    fd, tmp_path = tempfile.mkstemp(
        prefix=os.path.basename(path) + '.', suffix='.tmp', dir=os.path.dirname(path)
    )
    os.close(fd)
    try:
        pq.write_table(
            table,
            tmp_path,
            compression=COMPRESSION,
            compression_level=COMPRESSION_LEVEL,
            coerce_timestamps='us',
            data_page_size=8 * 1024 * 1024,
        )
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    return old_size, os.path.getsize(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        '--root', default=BASE_DIR,
        help=f'Root directory to walk (default: {BASE_DIR})',
    )
    ap.add_argument(
        '--apply', action='store_true',
        help='Actually rewrite files. Without this flag the script only reports sizes.',
    )
    ap.add_argument(
        '--limit', type=int, default=0,
        help='Process at most N files (for spot-checking). 0 = no limit.',
    )
    args = ap.parse_args()

    root = args.root
    parquet_files = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith('.parquet'):
                parquet_files.append(os.path.join(dirpath, fn))
    parquet_files.sort()

    if args.limit:
        parquet_files = parquet_files[:args.limit]

    print(f'[scan] root={root}  files={len(parquet_files)}  mode={"APPLY" if args.apply else "DRY-RUN"}')
    total_old = 0
    total_new = 0
    t0 = time.time()
    for i, path in enumerate(parquet_files, 1):
        try:
            if args.apply:
                old_b, new_b = rewrite_one(path)
            else:
                old_b = os.path.getsize(path)
                new_b = old_b  # nothing changes in dry-run
        except Exception as e:
            print(f'  [{i}/{len(parquet_files)}] FAILED {path}: {e}')
            continue
        total_old += old_b
        total_new += new_b
        if i % 50 == 0 or i == len(parquet_files):
            elapsed = time.time() - t0
            speed = i / elapsed if elapsed > 0 else 0
            print(
                f'  [{i}/{len(parquet_files)}] '
                f'old={total_old/1024/1024:.1f}MB new={total_new/1024/1024:.1f}MB '
                f'ratio={total_new/total_old*100:.1f}%  {speed:.1f} files/s'
            )

    saved = total_old - total_new
    pct = (1 - total_new / total_old) * 100 if total_old else 0
    print()
    print(f'[done] files={len(parquet_files)}  old={total_old/1024/1024:.1f}MB  '
          f'new={total_new/1024/1024:.1f}MB  saved={saved/1024/1024:.1f}MB ({pct:.1f}%)  '
          f'elapsed={time.time()-t0:.1f}s')
    if not args.apply:
        print('[note] dry-run only. Re-run with --apply to actually rewrite files.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
