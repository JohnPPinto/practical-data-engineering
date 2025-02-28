import argparse
import os
import sys
from time import perf_counter

import pandas as pd
import pyarrow.parquet as pq
import requests
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


def main(params):
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    host = os.environ.get("PG_HOST")
    port = os.environ.get("PG_PORT")
    database = os.environ.get("POSTGRES_DB")
    table = params.table
    url = params.url

    # Creating a data directory
    data_dir = "./nyc_taxi_data/"
    if not os.path.exists(path=data_dir):
        os.makedirs(name=data_dir)

    # Getting the file name from URL
    file_name = data_dir + url.split("/")[-1].strip()
    print(f"Downloading {file_name} ...")

    # Downloading the file using the URL
    response = requests.get(url)
    if response.ok and response.status_code == 200:
        with open(file=file_name, mode="wb+") as file:
            file.write(response.content)
        print(f"File has been downloaded to {file_name}\n")
    else:
        print(
            "Error: Received an error while connecting to the URL with "
            "status code: {response.status_code}\n"
        )
        sys.exit()

    # Creating sql engine
    database_url = URL.create(
        drivername="postgresql",
        username=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )
    engine = create_engine(url=database_url)

    # Read file based on csv or parquet
    if ".csv" in file_name:
        df = pd.read_csv(file_name, nrows=10)
        df_iter = pd.read_csv(file_name, iterator=True, chunksize=100000)
    elif ".parquet" in file_name:
        file = pq.ParquetFile(file_name)
        df = next(file.iter_batches(batch_size=10)).to_pandas()
        df_iter = file.iter_batches(batch_size=100000)
    else:
        print("Error. Only .csv or .parquet files allowed.")
        sys.exit()

    # Create the table
    df.head(0).to_sql(name=table, con=engine, if_exists="replace")

    # Insert values
    t_start = perf_counter()

    for i, batch in enumerate(df_iter, 1):
        if ".parquet" in file_name:
            batch_df = batch.to_pandas()
        else:
            batch_df = batch

        print(f"inserting batch {i}...")

        b_start = perf_counter()
        batch_df.to_sql(name=table, con=engine, if_exists="append")
        b_end = perf_counter()

        print(f"inserted! time taken {b_end-b_start:10.3f} seconds.\n")

    t_end = perf_counter()
    print(f"Completed! Total time taken was {t_end-t_start:10.3f} seconds")


if __name__ == "__main__":
    # Parsing arguments
    parser = argparse.ArgumentParser(
        description="Loading data from .parquet file link to a Postgres database."
    )

    parser.add_argument("--table", help="Destination table name for Postgres.")
    parser.add_argument("--url", help="URL for .parquet file.")

    args = parser.parse_args()
    main(args)
