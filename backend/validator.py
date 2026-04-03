# backend/validator.py

import json

class CompilerValidator:
    @staticmethod
    def validate(raw_sql_result, generated_python_result):
        """
        Compares two lists of dictionaries, independent of row order.
        """
        if len(raw_sql_result) != len(generated_python_result):
            return False, f"Row count mismatch: SQL({len(raw_sql_result)}) vs Python({len(generated_python_result)})"

        try:
            # 1. Convert each dictionary to a sorted JSON string to make them hashable/sortable
            # 2. Sort the entire list of strings
            sql_sorted = sorted([json.dumps(row, sort_keys=True) for row in raw_sql_result])
            py_sorted = sorted([json.dumps(row, sort_keys=True) for row in generated_python_result])

            # 3. Compare the sorted lists
            for i in range(len(sql_sorted)):
                if sql_sorted[i] != py_sorted[i]:
                    return False, f"Data mismatch in record set (Index {i} after sorting)"

            return True, "Success: Results are identical (Order-Independent)."
            
        except Exception as e:
            return False, f"Validation Error: {str(e)}"