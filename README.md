# ⚙️ SQL-to-Python Compiler Engine (LALREngine v2.0)

A custom, full-stack SQL compiler built from scratch. This project does not simply pass SQL to a database; it intercepts raw SQL, performs deep lexical and syntactic analysis, builds an Abstract Syntax Tree (AST), and dynamically generates Python code to execute the query against a PostgreSQL database. 

Paired with a modern React frontend, it acts as both a functional database client and an educational visualizer that exposes the inner workings of query planning and execution.

## 🚀 Architecture & The Compilation Pipeline

When a user submits a query, the engine routes it through a strict, 5-stage compilation pipeline:

1. **Lexical Analyzer (Scanner):** Tokenizes the raw SQL string, handling keywords, identifiers, literals, and operators while catching immediate lexical errors.
2. **Parser (Syntax Analyzer):** Validates the sequence of tokens against strict SQL grammar rules. It generates an initial Abstract Syntax Tree (AST) and catches syntax errors (e.g., missing `ON` clauses in joins, invalid keywords).
3. **Planner & Optimizer:** Restructures the AST for efficiency. It handles complex operations like resolving cross-table dot notation (`Table.column`), filtering, and subquery preparation.
4. **Code Generator (CodeGen):** Unwraps the AST into mathematically safe, edge-case-proof Python code. It handles:
   * Dynamic tuple extraction for multi-row `INSERT` operations.
   * `NULL` grouping and aggregation without raising `KeyError` or `NoneType` exceptions.
   * Division-by-zero safety guards.
   * ACID-compliant database connection management via `psycopg2`.
5. **Execution & Validation Engine:** Executes the generated Python code against a production Neon PostgreSQL database (21-entity schema) and strictly compares the Python-generated output against the Ground Truth database output to validate accuracy.

## ✨ Key Features

* **Strict Syntax Guardrails:** Catches and reports semantic and syntactic errors (e.g., `Unexpected 'FROMMM' at token IDENTIFIER`) gracefully in the UI without crashing the backend.
* **Complex Relational Logic:** Fully supports `INNER JOIN`, `CROSS JOIN`, `GROUP BY`, `HAVING`, `ORDER BY`, and `LIMIT`.
* **Data Mutation Handling:** Safely translates and commits DDL/DML queries (`CREATE`, `DROP`, `INSERT`, `UPDATE`, `DELETE`) with full database transaction support.
* **Interactive React Visualizer:** A stunning, three-pane developer UI that features an "Inspect Stages" modal. Users can visually explore the raw Tokens, the JSON/Visual AST trees, the Optimizer plan, and the final CodeGen output.

## 🛠️ Tech Stack

* **Backend Environment:** Python 3.x
* **API Framework:** FastAPI (RESTful endpoints for `/compile` and `/execute`)
* **Database Engine:** PostgreSQL (Serverless via Neon DB)
* **Database Driver:** `psycopg2` (with `RealDictCursor` for JSON serialization)
* **Frontend:** React.js (Bootstrapped with Vite)
* **UI/UX:** Custom CSS/Tailwind with interactive tree visualizations.

## 📦 Setup & Installation

### 1. Database Configuration
Ensure you have a PostgreSQL database running (or a Neon DB connection string).
Add your connection string to the backend environment variables or configuration file.

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fastapi uvicorn psycopg2-binary pydantic
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Access the UI at `http://localhost:5173`.

## 🧪 Master Test Suite

The engine is battle-tested against edge cases. Here are a few queries to demonstrate its power:

**The Happy Path (Joins & Aggregation)**
```sql
SELECT Courses.courseName, COUNT(Students.studentId) AS total_students 
FROM Students 
JOIN Courses ON Students.courseId = Courses.courseId 
GROUP BY Courses.courseName;
```

**The Edge Case (NULL Grouping)**
```sql
SELECT category, COUNT(id) AS total_items 
FROM null_group_test 
GROUP BY category;
```

**The Safety Net (Syntax Error Catching)**
```sql
SELECT * FROMMM Students WHERE year = 2;
```

## 👨‍💻 Author
Built from scratch as an exploration into database internals, meta-programming, and compiler theory.

