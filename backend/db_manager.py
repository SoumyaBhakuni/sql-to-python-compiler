import psycopg2
import re
from psycopg2.extras import RealDictCursor

class DatabaseManager:
    def __init__(self, connection_string):
        self.conn_string = connection_string

    def get_connection(self):
        return psycopg2.connect(self.conn_string)

    def get_schema(self):
        """
        Dynamically fetches table and column names from 
        information_schema to feed the Semantic Analyzer.
        """
        schema = {}
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Fetches EVERY table and column in the public schema
            query = """
                SELECT table_name, column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
            """
            cur.execute(query)
            rows = cur.fetchall()
            
            for row in rows:
                table = row['table_name']
                column = row['column_name']
                if table not in schema:
                    schema[table] = []
                schema[table].append(column)
                
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Schema Fetch Error: {e}")
        return schema

    def execute_raw_sql(self, sql):
        """
        Executes the original SQL with Case-Sensitive protection.
        Automatically quotes table names to match the 21-entity PascalCase schema.
        """
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # --- CASE SENSITIVITY LOGIC ---
            # This regex finds table names after FROM or JOIN and wraps them in " ".
            # Example: FROM Students -> FROM "Students"
            quoted_sql = re.sub(
                r'(FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)', 
                r'\1 "\2"', 
                sql, 
                flags=re.IGNORECASE
            )
            
            # Optional: Also quote specific PascalCase columns if needed
            # quoted_sql = re.sub(r'SELECT\s+([a-zA-Z_][a-zA-Z0-9_]*)', r'SELECT "\1"', quoted_sql, flags=re.IGNORECASE)

            cur.execute(quoted_sql)
            results = cur.fetchall()
            return results
        except Exception as e:
            # Re-raise with a descriptive prefix for the Frontend error state
            raise Exception(f"PostgreSQL Execution Error: {str(e)}")
        finally:
            cur.close()
            conn.close()