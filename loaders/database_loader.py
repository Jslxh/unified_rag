from pathlib import Path
from sqlalchemy import inspect, text, create_engine
from typing import Optional, List

class DatabaseLoader:
    """Loader for SQLite and SQL databases"""

    def __init__(self, db_path: str = "data/data.db"):
        self.db_path = db_path
        self.engine = None

    def connect(self, db_path: Optional[str] = None):
        """Connect to SQLite database"""
        try:
            path = db_path or self.db_path
            connection_string = f"sqlite:///{path}"
            self.engine = create_engine(connection_string)
            return True
        except Exception as e:
            raise ValueError(f"Failed to connect to database: {e}")

    def load_table(self, table_name: str, limit: int = 100) -> list:
        """Load data from a specific table"""
        if not self.engine:
            raise RuntimeError("Not connected to database. Call connect() first.")

        try:
            with self.engine.connect() as conn:
                # Get table schema
                inspector = inspect(self.engine)
                columns = inspector.get_columns(table_name)
                column_names = [col['name'] for col in columns]

                # Get row count
                row_count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = row_count_result.scalar()

                # Get sample data
                query = f"SELECT * FROM {table_name} LIMIT {limit}"
                result = conn.execute(text(query))
                rows = result.fetchall()

                # Format as readable text
                content_parts = [
                    f"TABLE: {table_name}",
                    f"Total Rows: {row_count}",
                    f"Columns: {', '.join(column_names)}",
                    "-" * 80,
                    "SCHEMA:"
                ]

                for col in columns:
                    content_parts.append(f"  {col['name']}: {col['type']}")

                content_parts.append("\nSAMPLE DATA:")
                for row in rows:
                    row_text = " | ".join([f"{col_names[i]}: {val}" for i, val in enumerate(row)])
                    content_parts.append(f"  {row_text}")

                if row_count > limit:
                    content_parts.append(f"\n... and {row_count - limit} more rows")

                content = "\n".join(content_parts)

                docs = [{
                    "content": content,
                    "metadata": {
                        "source": f"{Path(self.db_path).name}::{table_name}",
                        "type": "database_table",
                        "table": table_name,
                        "row_count": row_count,
                        "column_count": len(column_names)
                    }
                }]

                return docs

        except Exception as e:
            raise ValueError(f"Error loading table {table_name}: {e}")

    def list_tables(self) -> List[str]:
        """List all tables in the database"""
        if not self.engine:
            raise RuntimeError("Not connected to database. Call connect() first.")

        try:
            inspector = inspect(self.engine)
            return inspector.get_table_names()
        except Exception as e:
            raise ValueError(f"Error listing tables: {e}")

    def load_all_tables(self, limit: int = 50) -> list:
        """Load all tables from the database"""
        try:
            tables = self.list_tables()
            all_docs = []

            for table_name in tables:
                docs = self.load_table(table_name, limit=limit)
                all_docs.extend(docs)

            return all_docs

        except Exception as e:
            raise ValueError(f"Error loading all tables: {e}")


def load_database_file(file_path: str, table_name: Optional[str] = None) -> list:
    """
    Load data from SQLite database file.
    If table_name is specified, loads only that table.
    Otherwise loads all tables.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Database file {file_path} not found")

    try:
        loader = DatabaseLoader(str(path))
        loader.connect(str(path))

        if table_name:
            return loader.load_table(table_name)
        else:
            return loader.load_all_tables()

    except Exception as e:
        raise ValueError(f"Error loading database: {e}")
