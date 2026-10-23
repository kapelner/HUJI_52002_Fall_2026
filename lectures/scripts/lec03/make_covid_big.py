"""Stack covid.csv N times into a big dataset, to see what happens when data is large.

Writes covid_big/copy=0/part-0.parquet, covid_big/copy=1/part-0.parquet, ... (a folder
of Parquet files, one per copy) and, with --csv, the same rows as one big covid_big.csv.

Usage:  python3 make_covid_big.py covid.csv 50 --csv
"""
import argparse
import os

import pyarrow as pa
import pyarrow.csv as pc
import pyarrow.parquet as pq

ap = argparse.ArgumentParser()
ap.add_argument("csv_in")
ap.add_argument("n_copies", type=int)
ap.add_argument("--csv", action="store_true", help="also write covid_big.csv")
args = ap.parse_args()

# read once, with fips as text (it is a code, not a number)
tbl = pc.read_csv(args.csv_in, convert_options=pc.ConvertOptions(column_types={"fips": pa.string()}))
schema = tbl.schema.append(pa.field("copy", pa.int32()))
# quoting_style="none": no quotes at all (pyarrow otherwise quotes every string, and then awk sees "Texas" with the quotes). Safe here: no value contains a comma
writer = pc.CSVWriter("covid_big.csv", schema, write_options=pc.WriteOptions(quoting_style="none")) if args.csv else None

for k in range(args.n_copies):
    part = tbl.append_column("copy", pa.array([k] * tbl.num_rows, pa.int32()))
    os.makedirs(f"covid_big/copy={k}", exist_ok=True)           # folder name copy=k : a "hive partition"
    pq.write_table(part, f"covid_big/copy={k}/part-0.parquet", compression="zstd")
    if writer:
        writer.write_table(part)
if writer:
    writer.close()
print("rows:", args.n_copies * tbl.num_rows)
