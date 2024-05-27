import pandas as pd
import os
from sqlalchemy import create_engine
import time


class DataLoader:
    def __init__(self, color, year, user, password, port, db, tablename, month, host):
        self.color = color
        self.year = year
        self.password = password
        self.port = port
        self.user = user
        self.db = db
        self.tablename = tablename
        self.month = month
        self.host = host

    def download_data(self, year, month, color):
        month = int(month)
        url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{color}_tripdata_{year}-{month:02}.parquet"
        filename = f'{color}/{color}_tripdata_{year}-{month:02}.parquet'

        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)  # Ensure directory exists
            os.system(f"wget {url} -O {filename}")
        except Exception as e:
            raise Exception("An error occurred while trying to download the data and make the directories")

        return filename

    def read_data(self, filename):
        if filename:
            try:
                df_iter = pd.read_parquet(filename, iterator=True)  # Remove chunksize parameter
                return df_iter
            except Exception as e:
                raise Exception("Error reading data")

    def create_connection(self):
        postgres_url = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"
        try:
            engine = create_engine(postgres_url)
            engine.connect()
            return engine
        except Exception as e:
            raise Exception("Error creating database connection")

    def create_table_load_data(self, df_iter, tablename, engine):
        if df_iter:
            try:
                df_iter.head(n=0).to_sql(name=tablename, con=engine, if_exists="replace", index=False)
                for chunk in df_iter:
                    t_start = time.time()
                    chunk.to_sql(name=tablename, con=engine, if_exists="append", index=False)
                    t_stop = time.time()
                    print(f"Inserted another chunk, it took {(t_stop - t_start):.0f} seconds")
                print("All data has been loaded")
            except Exception as e:
                raise Exception("Error loading data into database")


if __name__ == "__main__":
    color = 'yellow'
    year = 2024
    password = "root"
    port = 5432
    user = "root"
    db = "newyorktaxi"
    tablename = f"{color}_tripdata"
    month = 1
    host = "172.19.0.2"

    data = DataLoader(color, year, user, password, port, db, tablename, month, host)

    filename = data.download_data(year, month, color)
    df_iter = data.read_data(filename)
    engine = data.create_connection()
    data.create_table_load_data(df_iter, tablename, engine)
