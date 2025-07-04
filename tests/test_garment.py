import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import polars as pl

from core.domain.garment import Garment
from core.domain.models import Base, Garment as GarmentModel, Delta, BaseMeasurement

@pytest.fixture
def db_session() -> Session:
    '''
    Create temporary in-memory database session and seed it with data for each test.
    '''
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    tshirt_measurements = {
        "Shoulder width": 46.0,
        "Chest circumference": 110.0,
    }
    tshirt_deltas = {
        "Shoulder width": {"XS": -4.0, "S": -2.0, "M": 0.0, "L": 2.0, "XL": 4.0},
        "Chest circumference": {"XS": -8.0, "S": -4.0, "M": 0.0, "L": 4.0, "XL": 8.0},
    }
    Garment.create_new_garment(
        db_session=session,
        garment_type="tshirt",
        base_size="M",
        measurements=tshirt_measurements,
        deltas=tshirt_deltas
    )

    try:
        yield session
    finally:
        session.close()

def test_override_non_base(db_session: Session):
    """
    Test override function when changing a non-base size.
    """

    shirt = Garment(db_session, garment_id=1)
    assert shirt.base_size == "M" # Verify that shirt was loaded correctly

    # This is what the function is testing
    shirt.override(measurement="Shoulder width", size="L", new_value=51.0)

    # Check if final size was changed
    final_l_shoulder = shirt.sizes.filter(
        pl.col("Measurement") == "Shoulder width"
    ).select("L").item()
    assert final_l_shoulder == 51.0

    # Check if delta was changed
    db_delta = db_session.query(Delta).filter_by(
        garment_id=1,
        measurement_name="Shoulder width",
        size="L"
    ).one()
    assert db_delta.delta_value == 5.0

def test_override_base(db_session: Session):
    """
    Test override function when changing a base size.
    """

    shirt = Garment(db_session, garment_id=1)
    assert shirt.base_size == "M"

    shirt.override(measurement="Chest circumference", size="M", new_value=111.0)

    # Check if base value was correctly modified
    db_base_measurement = db_session.query(BaseMeasurement).filter_by(
        garment_id=1,
        measurement_name="Chest circumference"
    ).one()
    assert db_base_measurement.value == 111.0

   # Check if a non-base size updated alongside the change
    final_l_chest = shirt.sizes.filter(
        pl.col("Measurement") == "Chest circumference"
    ).select("L").item()
    assert final_l_chest == 115.0

def test_change_base(db_session: Session):
    """
    Test the change_base function
    """

    shirt = Garment(db_session, garment_id=1)
    assert shirt.base_size == "M"

    shirt.change_base_size("L")

    # Check that no recalculations were triggered
    final_l_chest = shirt.sizes.filter(
        pl.col("Measurement") == "Chest circumference"
    ).select("L").item()
    assert final_l_chest == 114.0

    # Check that deltas have been centered around new base size (L)
    final_delta_chest = db_session.query(Delta).filter_by(
        garment_id=1,
        measurement_name="Shoulder width",
        size="L"
    ).one()
    assert final_delta_chest.delta_value == 0.0
