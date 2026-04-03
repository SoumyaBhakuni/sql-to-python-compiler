# backend/validator.py

class CompilerValidator:
    @staticmethod
    def validate(raw_sql_result, generated_python_result):
        """
        Compares two lists of dictionaries. 
        Returns True if they are identical in content.
        """
        if len(raw_sql_result) != len(generated_python_result):
            return False, f"Row count mismatch: SQL({len(raw_sql_result)}) vs Python({len(generated_python_result)})"

        # Sort both lists by a common key or stringify to compare content-wise
        # For PBL, we do a deep comparison
        for i in range(len(raw_sql_result)):
            if raw_sql_result[i] != generated_python_result[i]:
                return False, f"Data mismatch at row {i}"

        return True, "Success: Results are 100% identical."