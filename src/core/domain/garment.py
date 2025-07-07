import polars as pl
import polars.selectors as cs
import os
import json
import logging
from pathlib import Path

from .exceptions import GarmentNotFoundError
from .models import Garment as GarmentModel, BaseMeasurement, Delta
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.DEBUG)


class Garment:
    def __init__(self, db_session: Session, garment_id: int):
        self.session = db_session
        self.garment_model = self.session.query(GarmentModel).filter_by(id=garment_id).one()

        self.base_size = self.garment_model.base_size

        self.refresh_dataframes()

    def refresh_dataframes(self):
        """Reloads all in-memory data from the database and recalculates sizes."""
        self.base = self._load_base()
        self.deltas = self._load_deltas()
        self.sizes = self._calculate_sizes()

    def _load_base(self):
        """Converts the loaded SQLAlchemy BaseMeasurement objects into a Polars DataFrame."""
        data = [
            {"Measurement": m.measurement_name, "value": m.value}
            for m in self.garment_model.base_measurements
        ]
        if not data:
            return pl.DataFrame({"Measurement": []})

        base_df = pl.DataFrame(data)
        final_df = base_df.select("Measurement")

        for size in ["XS", "S", "M", "L", "XL"]:
            final_df = final_df.with_columns(base_df.get_column("value").alias(size))
        return final_df

    def _load_deltas(self):
        """Converts the loaded SQLAlchemy Delta objects into a Polars DataFrame."""
        data = [
            {"Measurement": d.measurement_name, "size": d.size, "delta_value": d.delta_value}
            for d in self.garment_model.deltas
        ]
        if not data:
            return pl.DataFrame({"Measurement": []})

        deltas_df = pl.DataFrame(data)
        unordered_df = deltas_df.pivot(
            values="delta_value",
            index="Measurement",
            columns="size"
        )

        # Reorder
        size_order = ["XS", "S", "M", "L", "XL"]
        return unordered_df.select(["Measurement"] + size_order)

    def _calculate_sizes(self):
        base_numeric = self.base.select(cs.numeric())
        deltas_numeric = self.deltas.select(cs.numeric())
        numeric_sizes = base_numeric + deltas_numeric
        final_sizes = pl.concat([self.base.select("Measurement"), numeric_sizes], how="horizontal")
        final_sizes = final_sizes.with_columns(pl.when(cs.numeric() > 0).then(cs.numeric()).otherwise(pl.lit(None)))
        return final_sizes

    def change_base_size(self, new_base_size):
        self.garment_model.base_size = new_base_size
        self.base_size = new_base_size

        # Group deltas by measurement name for easier processing
        deltas_by_measurement = {}
        for d in self.garment_model.deltas:
            deltas_by_measurement.setdefault(d.measurement_name, []).append(d)

        for measurement_name, deltas_list in deltas_by_measurement.items():
            reference_delta_value = 0
            # Get the new base size's delta value
            for d in deltas_list:
                if d.size == new_base_size:
                    reference_delta_value = d.delta_value
                    break

            # Subtract by reference_delta_value to recenter deltas
            for d in deltas_list:
                d.delta_value -= reference_delta_value

        self.session.commit()
        self.deltas = self._load_deltas()

    def recalculate_measurement(self, measurement : str):
        """
        Refreshes a single measurement row in the self.sizes table by
        re-calculating it from the current base and deltas.
        """
        # Get the single row for the specified measurement from the base and deltas tables
        base_row = self.base.filter(pl.col("Measurement") == measurement)
        deltas_row = self.deltas.filter(pl.col("Measurement") == measurement)

        new_size_row = self._calculate_sizes_for_row(base_row, deltas_row)
        rows_to_keep = self.sizes.filter(pl.col("Measurement") != measurement)

        # Define the consistent Enum type based on the master order.
        measurement_order = self.base.get_column("Measurement").to_list()
        enum_type = pl.Enum(categories=measurement_order)

        # Ensure both DataFrames have the same Enum type before concatenation.
        rows_to_keep = rows_to_keep.with_columns(pl.col("Measurement").cast(enum_type))
        new_size_row = new_size_row.with_columns(pl.col("Measurement").cast(enum_type))

        # Combine the old rows with the newly calculated one
        new_sizes_df = pl.concat([rows_to_keep, new_size_row])

        self.sizes = new_sizes_df.with_columns(
            pl.col("Measurement").cast(enum_type)
        ).sort("Measurement")

    def _calculate_sizes_for_row(self, base_row: pl.DataFrame, deltas_row: pl.DataFrame) -> pl.DataFrame:
        """Helper to calculate sizes for a single row DataFrame."""
        base_numeric = base_row.select(cs.numeric())
        deltas_numeric = deltas_row.select(cs.numeric())
        numeric_sizes = base_numeric + deltas_numeric
        final_row = pl.concat([base_row.select("Measurement"), numeric_sizes], how="horizontal")
        final_row = final_row.with_columns(pl.when(cs.numeric() > 0).then(cs.numeric()).otherwise(pl.lit(None)))
        return final_row


    def override(self, measurement: str, size: str, new_value: float):
        if size == self.base_size:
            db_measurement = self.session.query(BaseMeasurement).filter_by(
                garment_id=self.garment_model.id,
                measurement_name=measurement
            ).one_or_none()

            if db_measurement:
                db_measurement.value = new_value

            self.session.commit()
            self.refresh_dataframes()

        else:
            db_delta = self.session.query(Delta).filter_by(
                garment_id=self.garment_model.id,
                measurement_name=measurement,
                size=size
            ).one_or_none()

            if db_delta:
                base_measurement = self.session.query(BaseMeasurement.value).filter_by(
                    garment_id=self.garment_model.id,
                    measurement_name=measurement
                ).scalar()
                new_delta = new_value - base_measurement
                db_delta.delta_value = new_delta

            self.session.commit()
            # Only update the deltas and the single cell in the sizes table.
            self.deltas = self._load_deltas()
            self.sizes = self.sizes.with_columns(
                pl.when(pl.col("Measurement") == measurement)
                .then(pl.lit(new_value))
                .otherwise(pl.col(size))
                .alias(size)
            )


    @staticmethod
    def list_garments(db_session: Session):
        """Queries the database and returns a list of all garments with their IDs and types."""
        garments = db_session.query(
            GarmentModel.id,
            GarmentModel.garment_type
        ).order_by(GarmentModel.id).all()

        if not garments:
            logging.log(10, "No garments found in the database.")
            return []

        logging.log(10, "\n--- Available Garments in Database ---")
        for garment_id, garment_type in garments:
            logging.log(10, f"ID: {garment_id}, Type: {garment_type}")

        return garments

    @staticmethod
    def create_new_garment(db_session: Session, garment_type: str, base_size: str, measurements: dict, deltas: dict):
        """A static method to create a brand new garment in the database."""

        garment_already_exists = db_session.query(GarmentModel).filter_by(garment_type=garment_type).one_or_none()

        if garment_already_exists:
            raise DuplicateGarmentError(f"{garment_type} already in database.")

        new_garment = GarmentModel(garment_type=garment_type, base_size=base_size)
        db_session.add(new_garment)

        for name, value in measurements.items():
            new_measurement = BaseMeasurement(measurement_name=name, value=value, garment=new_garment)
            db_session.add(new_measurement)

        for name, size_deltas in deltas.items():
            for size, delta_value in size_deltas.items():
                new_delta = Delta(measurement_name=name, size=size, delta_value=delta_value, garment=new_garment)
                db_session.add(new_delta)

        db_session.commit()
        return new_garment.id

    @staticmethod
    def remove_garment(db_session: Session, garment_id: int):
        """Finds and removes a garment and all its associated data from the database."""
        garment_to_delete = db_session.query(GarmentModel).filter_by(id=garment_id).one_or_none()

        if not garment_to_delete:
            raise GarmentNotFoundError(f"Garment with ID {garment_id} not found.")

        db_session.delete(garment_to_delete)
        db_session.commit()
