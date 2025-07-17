from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import JSON

Base = declarative_base()

class Garment(Base):
    __tablename__ = 'garments'
    id = Column(Integer, primary_key=True)
    garment_type = Column(String, nullable=False, unique=True)
    base_size = Column(String, nullable=False)
    sizes_to_order = Column(JSON, nullable=False, default=[])
    base_measurements = relationship("BaseMeasurement", back_populates="garment", cascade="all, delete-orphan")
    deltas = relationship("Delta", back_populates="garment", cascade="all, delete-orphan")

    # Representation with information about the garment
    def __repr__(self):
        return f"<Garment(id={self.id}, type='{self.garment_type}', base_size='{self.base_size}')>"

class BaseMeasurement(Base):
    __tablename__ = 'base_measurements'

    id = Column(Integer, primary_key=True)
    measurement_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)

    garment_id = Column(Integer, ForeignKey('garments.id'), nullable=False)

    garment = relationship("Garment", back_populates="base_measurements")

    def __repr__(self):
        return f"<BaseMeasurement(name='{self.measurement_name}', value={self.value})>"

class Delta(Base):
    __tablename__ = 'deltas'

    id = Column(Integer, primary_key=True)
    measurement_name = Column(String, nullable=False)
    size = Column(String, nullable=False)
    delta_value = Column(Float, nullable=False)

    garment_id = Column(Integer, ForeignKey('garments.id'), nullable=False)

    garment = relationship("Garment", back_populates="deltas")

    def __repr__(self):
        return f"<Delta(name='{self.measurement_name}', size='{self.size}', delta={self.delta_value})>"

# INFO:
# Garment Model: Main table; stores core information about each garment.
#
# - id (Integer, Primary Key)
#
# - garment_type (String, e.g., "tshirt", "pants")
#
# - base_size (String, e.g., "M")
#
# BaseMeasurement Model: Holds base measurements; has a many-to-one relationship with Garment (one garment has many base measurements).
#
# - id (Integer, Primary Key)
#
# - measurement_name (String, e.g., "Shoulder width")
#
# - value (Float)
#
# - garment_id (Integer, Foreign Key linking to Garment.id)
#
# Delta Model: Holds deltas; also has a many-to-one relationship with Garment.
#
# - id (Integer, Primary Key)
#
# - measurement_name (String)
#
# - size (String, e.g., "XS", "S")
#
# - delta_value (Float)
#
# - garment_id (Integer, Foreign Key linking to Garment.id)