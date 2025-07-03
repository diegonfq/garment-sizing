from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import os
from src.core.domain.sizes import Garment
from src.core.domain.models import Base

import logging
logging.basicConfig(level=logging.DEBUG)

# --- 1. DATABASE SETUP ---
# This part sets up the connection to your SQLite database.
# In a real application, this might be in a separate config file.

DATABASE_FILE = "data/garment_data.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# The engine is the core interface to the database.
engine = create_engine(DATABASE_URL)

# A SessionLocal class is a factory for creating new database sessions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure the data directory exists
os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)

# Create all tables defined in your models (if they don't exist yet)
# This is equivalent to running 'alembic upgrade head' for the first time.
Base.metadata.create_all(bind=engine)


def get_db_session() -> Session:
    """Helper function to get a new database session."""
    return SessionLocal()


def setup_initial_data():
    """
    Checks if any garments exist and, if not, creates a sample
    T-shirt to ensure the demo has data to work with.
    """
    db = get_db_session()
    Garment.remove_garment(db, 1)

    # Use the updated function name: list_garments
    existing_garments = Garment.list_garments(db)
    if not existing_garments:
        logging.log(10,"\nDatabase is empty. Creating a sample T-shirt...")

        # Define the data for a new T-shirt
        tshirt_measurements = {
            "Shoulder width": 46.0,
            "Chest circumference": 110.0,
            "Waist circumference": 102.0,
            "Hip circumference": 108.0
        }
        tshirt_deltas = {
            "Shoulder width": {"XS": -4.0, "S": -2.0, "M": 0.0, "L": 2.0, "XL": 4.0},
            "Chest circumference": {"XS": -8.0, "S": -4.0, "M": 0.0, "L": 4.0, "XL": 8.0},
            "Waist circumference": {"XS": -6.0, "S": -3.0, "M": 0.0, "L": 3.0, "XL": 6.0},
            "Hip circumference": {"XS": -6.0, "S": -3.0, "M": 0.0, "L": 3.0, "XL": 6.0}
        }

        # Use the static method to create it in the database
        Garment.create_new_garment(
            db_session=db,
            garment_type="tshirt",
            base_size="M",
            measurements=tshirt_measurements,
            deltas=tshirt_deltas
        )
    db.close()


def main():
    """Main function to run the demonstration."""

    # --- 2. SETUP & LISTING ---
    setup_initial_data()

    db = get_db_session()
    # Use the updated function name: list_garments
    available_garments = Garment.list_garments(db)
    if not available_garments:
        logging.log(10,"Setup failed. Exiting.")
        db.close()
        return

    # We'll work with the first garment found in the database
    garment_id_to_load = available_garments[0][0]
    db.close()

    # --- 3. LOADING & INITIAL STATE ---
    logging.log(10,f"\n--- Loading Garment ID: {garment_id_to_load} ---")
    db = get_db_session()
    shirt = Garment(db, garment_id_to_load)

    logging.log(10,"\n--- Initial Sizes (Base: M) ---")
    logging.log(10,shirt.sizes)
    logging.log(10,shirt.deltas)

    # --- 4. FEATURE DEMO: OVERRIDE A NON-BASE SIZE ---
    # This changes a delta rule.
    logging.log(10,"\n--- ACTION: Overriding 'L' Shoulder width to 51.0 (defines a new delta) ---")
    shirt.override("Shoulder width", "L", 51.0)
    logging.log(10,"\n--- Sizes after overriding 'L' ---")
    logging.log(10,shirt.sizes)
    logging.log(10,shirt.deltas)

    # --- 5. FEATURE DEMO: OVERRIDE A BASE SIZE ---
    # This changes an anchor value and recalculates other sizes in that row.
    logging.log(10,"\n--- ACTION: Overriding base 'M' Chest to 111.0 (defines a new anchor) ---")
    shirt.override("Chest circumference", "M", 111.0)
    logging.log(10,"\n--- Sizes after overriding 'M' ---")
    logging.log(10,shirt.sizes)

    # --- 6. FEATURE DEMO: CHANGE THE BASE SIZE ---
    # This changes the anchor size and recalculates all deltas.
    logging.log(10,"\n--- ACTION: Changing base size from 'M' to 'L' ---")
    shirt.change_base_size("L")

    logging.log(10,"\n--- Deltas after changing base to 'L' (Note 'L' column is now 0) ---")
    logging.log(10,shirt.deltas)

    logging.log(10,"\n--- Sizes after changing base to 'L' and making a change  to waist circumference ---")
    shirt.override("Waist circumference", "M", 110)
    logging.log(10,shirt.sizes)

    db.close()


if __name__ == "__main__":
    main()
