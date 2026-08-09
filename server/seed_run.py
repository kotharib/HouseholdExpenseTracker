"""Run database seeding explicitly: python -m app.seed_run"""
from sqlmodel import Session

from app.database import engine, init_db
from app.services.seed import run_seed


def main() -> None:
    init_db()
    with Session(engine) as session:
        run_seed(session)
        print("Database seeded successfully.")
        print("Admin login -> username: admin / password: admin123")
        print("Demo login  -> username: demo  / password: demo123")


if __name__ == "__main__":
    main()
