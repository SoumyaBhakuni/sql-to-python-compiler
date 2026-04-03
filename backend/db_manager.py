import psycopg2
import re
from psycopg2.extras import RealDictCursor

class DatabaseManager:
    def __init__(self, connection_string):
        self.conn_string = connection_string

    def get_connection(self):
        return psycopg2.connect(self.conn_string)

    def get_schema(self):
        schema = {}
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public'")
            for row in cur.fetchall():
                t, c = row['table_name'], row['column_name']
                if t not in schema: schema[t] = []
                schema[t].append(c)
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Schema Error: {e}")
        return schema

    def execute_raw_sql(self, sql):
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # Matches identifiers after FROM/JOIN and wraps them in " "
            quoted_sql = re.sub(r'(FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)', r'\1 "\2"', sql, flags=re.IGNORECASE)
            cur.execute(quoted_sql)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()