import os
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

# Enable CORS for React Frontend (Vite defaults to port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Explicitly allow Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB Manager (Replace with your NeonDB URI)
DATABASE_URL = os.getenv("DATABASE_URL")
db = DatabaseManager(DATABASE_URL)

class QueryRequest(BaseModel):
    sql: str

@app.post("/compile")
async def compile_sql(request: QueryRequest):
    """
    The full compilation pipeline. 
    Returns data for each stage to power the Frontend Visualizer.
    """
    try:
        raw_sql = request.sql.strip()
        if not raw_sql:
            raise ValueError("Empty query string.")

        # --- PHASE 1: LEXICAL ANALYSIS ---
        lexer.input(raw_sql)
        token_list = []
        # We re-tokenize to send the list to the UI
        temp_lexer = lexer.clone()
        temp_lexer.input(raw_sql)
        for tok in temp_lexer:
            token_list.append({"type": tok.type, "value": tok.value, "pos": tok.lexpos})

        # --- PHASE 2: LALR PARSING ---
        ast_root = parse_sql(raw_sql)
        if not ast_root:
            raise ValueError("Parser failed to generate an AST.")

        # --- PHASE 3: SEMANTIC ANALYSIS ---
        schema = db.get_schema()
        analyzer = SemanticAnalyzer(schema)
        analyzer.analyze(ast_root)

        # --- PHASE 4: QUERY PLANNING (IR) ---
        planner = QueryPlanner()
        logical_plan = planner.create_plan(ast_root)

        # --- PHASE 5: OPTIMIZATION ---
        optimizer = QueryOptimizer()
        optimized_plan = optimizer.optimize(logical_plan)

        # --- PHASE 6: CODE GENERATION ---
        generator = CodeGenerator()
        python_code = generator.generate(optimized_plan)

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
        # This returns the red error state for your Action Circle
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/execute")
async def execute_and_compare(request: QueryRequest):
    """
    Runs both the Raw SQL and the Generated Python code, 
    then validates them using the Validator.
    """
    try:
        # 1. Get Ground Truth from PostgreSQL
        sql_result = db.execute_raw_sql(request.sql)

        # 2. Re-compile to get the Python string
        ast = parse_sql(request.sql)
        plan = QueryOptimizer().optimize(QueryPlanner().create_plan(ast))
        python_script = CodeGenerator().generate(plan)

        # 3. Execute Generated Python Code 
        # FIX: We must provide psycopg2 to the execution environment
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Inject the modules into the globals dictionary
        exec_globals = {
            "psycopg2": psycopg2,
            "RealDictCursor": RealDictCursor,
            "__builtins__": __builtins__
        }
        local_scope = {}

        # Run the script string
        exec(python_script, exec_globals, local_scope)
        
        # Call the generated function (now visible in local_scope)
        python_result = local_scope['execute_compiled_query'](DATABASE_URL)

        # 4. Validate
        is_valid, message = CompilerValidator.validate(sql_result, python_result)

        return {
            "is_valid": is_valid,
            "message": message,
            "sql_output": sql_result[:10], 
            "python_output": python_result[:10]
        }
    except Exception as e:
        # This will now catch the 'psycopg2 not defined' error if it persists
        raise HTTPException(status_code=400, detail=f"Execution Error: {str(e)}")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)