from sqlalchemy import create_engine

engine = create_engine("sqlite:///app/data/db.sqlite3")
with engine.connect() as conn:
    result = conn.execute("SELECT 1")
    print(result.fetchone())
