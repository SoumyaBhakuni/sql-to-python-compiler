import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict
from dotenv import load_dotenv

# Import your compiler pipeline components
from models import Node
from lexer import lexer
from parser import parse_sql
from semantic import SemanticAnalyzer
from planner import QueryPlanner
from optimizer import QueryOptimizer
from codegen import CodeGenerator
from db_manager import DatabaseManager
from validator import CompilerValidator

load_dotenv()
app = FastAPI(title="SQL-to-Python Compiler API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")
db = DatabaseManager(DATABASE_URL)

class QueryRequest(BaseModel):
    sql: str

@app.post("/compile")
async def compile_sql(request: QueryRequest):
    """PHASE 1-6: Returns internal states and generated code ONLY."""
    try:
        raw_sql = request.sql.strip()
        if not raw_sql:
            raise ValueError("Empty query string.")

        # Lexer
        lexer.input(raw_sql)
        token_list = []
        temp_lexer = lexer.clone()
        temp_lexer.input(raw_sql)
        for tok in temp_lexer:
            token_list.append({"type": tok.type, "value": tok.value, "pos": tok.lexpos})

        # Parser
        ast_root = parse_sql(raw_sql)
        
        # Semantic
        schema = db.get_schema()
        SemanticAnalyzer(schema).analyze(ast_root)

        # Planning & Optimization
        logical_plan = QueryPlanner().create_plan(ast_root)
        optimized_plan = QueryOptimizer().optimize(logical_plan)

        # CodeGen
        python_code = CodeGenerator().generate(optimized_plan)

        return {
            "status": "success",
            "stages": {
                "lexer": token_list,
                "parser": ast_root.to_dict(),
                "planner": logical_plan.to_dict() if hasattr(logical_plan, 'to_dict') else str(logical_plan),
                "optimizer": optimized_plan.to_dict() if hasattr(optimized_plan, 'to_dict') else str(optimized_plan),
                "codegen": python_code
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/execute/sql")
async def run_ground_truth(request: QueryRequest):
    """Triggered by 'RUN SQL' button."""
    try:
        sql_result = db.execute_raw_sql(request.sql)
        return {"status": "success", "sql_output": sql_result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL Error: {str(e)}")

@app.post("/execute/python")
async def run_compiled_logic(request: QueryRequest):
    """Triggered by 'RUN PYTHON' button. Also performs cross-validation."""
    try:
        # 1. Get SQL result for validation reference
        sql_result = db.execute_raw_sql(request.sql)

        # 2. Compile to get Python script
        ast = parse_sql(request.sql)
        plan = QueryOptimizer().optimize(QueryPlanner().create_plan(ast))
        python_script = CodeGenerator().generate(plan)

        # 3. Execution environment setup
        exec_globals = {
            "psycopg2": psycopg2, 
            "RealDictCursor": RealDictCursor, 
            "__builtins__": __builtins__
        }
        local_scope = {}
        
        # 4. Execute generated code
        exec(python_script, exec_globals, local_scope)
        python_result = local_scope['execute_compiled_query'](DATABASE_URL)

        # 5. Cross-check against SQL Ground Truth
        is_valid, message = CompilerValidator.validate(sql_result, python_result)

        return {
            "is_valid": is_valid,
            "message": message,
            "python_output": python_result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Python Execution Error: {str(e)}")

class ValidationRequest(BaseModel):
    sql_data: list
    python_data: list

@app.post("/execute/validate")
async def validate_results(request: ValidationRequest):
    """Triggered only by the manual VALIDATE button."""
    from validator import CompilerValidator
    is_valid, message = CompilerValidator.validate(request.sql_data, request.python_data)
    return {"is_valid": is_valid, "message": message}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)