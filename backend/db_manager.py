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
        clean_sql = sql.strip().upper().rstrip(';')
        if clean_sql == "SHOW TABLES":
            return self.get_tables_list()

        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            schema = self.get_schema()
            all_ids = list(schema.keys())
            for cols in schema.values():
                all_ids.extend(cols)
            
            all_ids = sorted(list(set(all_ids)), key=len, reverse=True)
            quoted_sql = sql
            
            for identifier in all_ids:
                if any(c.isupper() for c in identifier):
                    pattern = rf'\b{identifier}\b'
                    quoted_sql = re.sub(pattern, f'"{identifier}"', quoted_sql)

            quoted_sql = re.sub(r'(?i)\b(FROM|JOIN)\s+([a-zA-Z_]\w*)', r'\1 "\2"', quoted_sql)
            
            cur.execute(quoted_sql)
            
            # --- THE CRITICAL FIX ---
            conn.commit() # This saves INSERT/UPDATE/DELETE/CREATE to the database
            
            # Only try to fetch if the command actually returns rows (like SELECT)
            if cur.description:
                return cur.fetchall()
            else:
                return [{"status": "success", "message": "Command executed and committed."}]
                
        except Exception as e:
            conn.rollback() # Undo any partial changes on error
            return [{"error": str(e)}]
        finally:
            cur.close()
            conn.close()
            
    def get_tables_list(self):
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()