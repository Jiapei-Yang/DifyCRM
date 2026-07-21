from pathlib import Path
import argparse
import re

import mysql.connector


ROOT = Path(__file__).resolve().parents[1]


def split_sql(script: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_string = False
    quote = ""
    for char in script:
        if char in {"'", '"'}:
            if not in_string:
                in_string = True
                quote = char
            elif quote == char:
                in_string = False
        if char == ";" and not in_string:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(char)
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return [s for s in statements if not re.match(r"^\s*--", s)]


def run_script(cursor, path: Path) -> None:
    script = path.read_text(encoding="utf-8")
    for statement in split_sql(script):
        cursor.execute(statement)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Drop and recreate dify_crm")
    args = parser.parse_args()

    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="123456",
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
    )
    cursor = conn.cursor()
    if args.reset:
        cursor.execute("DROP DATABASE IF EXISTS dify_crm")
    run_script(cursor, ROOT / "sql" / "schema.sql")
    run_script(cursor, ROOT / "sql" / "seed.sql")
    conn.commit()
    cursor.close()
    conn.close()
    print("DifyCRM database initialized: dify_crm")


if __name__ == "__main__":
    main()
