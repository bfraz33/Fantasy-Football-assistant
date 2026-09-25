import json
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

def get_conn(path="config/snowflake.json"):
    with open(path) as f:
        return snowflake.connector.connect(**json.load(f))

def load_df(conn, df, table, mode="replace"):
    df=df.copy()
    df.columns = [c.upper() for c in df.columns]
    ok, _, nrows, _ = write_pandas(
        conn, df, table.upper(),
        auto_create_table=True, overwrite=(mode=="replace"),

    )
    print(f"{table}: loaded {nrows} rows" if ok else f"{table}: failed to load")