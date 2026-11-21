import re
import sqlite3
from contextlib import closing
from pathlib import Path

import ollama
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)
DATABASE_PATH = Path(__file__).resolve().with_name("Chinook_Sqlite.sqlite")
SCHEMA_TABLES = ("Customer", "Invoice", "InvoiceLine", "Track")


class QueryRequest(BaseModel):
    domanda: str


@app.get("/")
def read_root():
    return {"stato": "ok"}


@app.post("/query")
def query_database(request: QueryRequest):
    database_uri = f"file:{DATABASE_PATH.as_posix()}?mode=ro"
    with closing(sqlite3.connect(database_uri, uri=True)) as connection:
        schema_rows = {
            table: connection.execute(f'PRAGMA table_info("{table}")').fetchall()
            for table in SCHEMA_TABLES
        }
        foreign_key_rows = {
            table: [
                row
                for row in connection.execute(f'PRAGMA foreign_key_list("{table}")')
                if row[2] in SCHEMA_TABLES
            ]
            for table in SCHEMA_TABLES
        }

    schema = (
        "Tabelle e colonne:\n"
        + "\n".join(
            f"{table}({', '.join(f'{row[1]} {row[2]}' for row in rows)})"
            for table, rows in schema_rows.items()
        )
        + "\nChiavi esterne:\n"
        + "\n".join(
            f"{table}.{row[3]} -> {row[2]}.{row[4]}"
            for table, rows in foreign_key_rows.items()
            for row in rows
        )
    )
    response = ollama.chat(
        model="phi3",
        options={"temperature": 0},
        messages=[
            {
                "role": "system",
                "content": (
                    "Genera una sola query SQL SQLite di sola lettura usando lo schema "
                    "fornito. Rispondi esclusivamente con la query, senza spiegazioni "
                    "né blocchi Markdown. Usa esclusivamente le tabelle e le colonne "
                    "elencate nello schema. Non inventare tabelle o colonne.\n\n"
                    f"Schema:\n{schema}"
                ),
            },
            {"role": "user", "content": request.domanda},
        ],
    )
    sql = re.sub(
        r"\s*```$",
        "",
        re.sub(
            r"^```(?:sql)?\s*",
            "",
            response.message.content.strip(),
            flags=re.IGNORECASE,
        ),
    ).strip()

    if not re.match(r"^SELECT\b", sql, flags=re.IGNORECASE):
        raise HTTPException(
            status_code=400,
            detail="Errore di sicurezza: sono consentite solo query SELECT.",
        )

    try:
        with closing(sqlite3.connect(database_uri, uri=True)) as connection:
            connection.row_factory = sqlite3.Row
            results = [dict(row) for row in connection.execute(sql).fetchall()]
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Query SQL non valida: {exc}",
        ) from exc

    return {"query": sql, "risultati": results}
