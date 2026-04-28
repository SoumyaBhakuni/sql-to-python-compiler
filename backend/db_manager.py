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
        """
        Executes raw SQL by automatically quoting PascalCase identifiers 
        from the schema to support standard SQL syntax.
        """
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # 1. Fetch current schema identifiers
            schema = self.get_schema()
            all_ids = list(schema.keys())
            for cols in schema.values():
                all_ids.extend(cols)
            
            # 2. Sort by length descending to prevent partial matching (e.g., matching 'Id' in 'studentId')
            all_ids = sorted(list(set(all_ids)), key=len, reverse=True)
            
            quoted_sql = sql
            # 3. Automatically wrap known PascalCase identifiers in double quotes
            for identifier in all_ids:
                if any(c.isupper() for c in identifier):
                    # Use word boundaries to target exact matches
                    pattern = rf'\b{identifier}\b'
                    quoted_sql = re.sub(pattern, f'"{identifier}"', quoted_sql)

            # 4. Fallback for table-specific quotes after FROM or JOIN
            quoted_sql = re.sub(r'(?i)\b(FROM|JOIN)\s+([a-zA-Z_]\w*)', r'\1 "\2"', quoted_sql)
            
            cur.execute(quoted_sql)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()