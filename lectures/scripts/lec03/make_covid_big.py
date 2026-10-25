"""Stack covid.csv N times into a big dataset, to see what happens when data is large.

Writes one big covid_big.parquet (each copy is its own row group, so the file has N row
groups; the rows carry no marker of which copy they came from) and, with --csv, the same rows as one big covid_big.csv.

Usage:  python3 make_covid_big.py covid.csv 50 --csv
"""
import argparse
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
schema = tbl.schema
# quoting_style="none": no quotes at all (pyarrow otherwise quotes every string, and then awk sees "Texas" with the quotes). Safe here: no value contains a comma
writer = pc.CSVWriter("covid_big.csv", schema, write_options=pc.WriteOptions(quoting_style="none")) if args.csv else None

pq_writer = pq.ParquetWriter("covid_big.parquet", schema, compression="zstd")
for k in range(args.n_copies):
    pq_writer.write_table(tbl)             # one copy = one row group
    if writer:
        writer.write_table(tbl)
pq_writer.close()
if writer:
    writer.close()
print("rows:", args.n_copies * tbl.num_rows)
