import polars as pl
import polars.selectors as cs
import os
import json
import logging

class Garment:
    def __init__(self, measurement_labels, base_measurements, default_deltas, base_size="M"):
        self.measurement_labels = measurement_labels
        self.base_measurements_data = base_measurements
        self.default_deltas_data = default_deltas
        self.base_size = base_size

        self.base = self._set_base()
        self.deltas = self._set_deltas()

        self.sizes = self._calculate_sizes()

    def _set_base(self):
        base_measurements = self.base_measurements_data

        base = pl.DataFrame(
            {
                "Measurement": self.measurement_labels,
                "XS": base_measurements,
                "S": base_measurements,
                "M": base_measurements,
                "L": base_measurements,
                "XL": base_measurements
            }
        )
        return base

    def _set_deltas(self):
        size_chart = {"XS": 0, "S": 1, "M": 2, "L": 3, "XL": 4}
        base_size = size_chart[self.base_size]

        default_base_deltas = self.default_deltas_data
        deltas = pl.DataFrame(
            {
                "Measurement": self.measurement_labels,
                "XS": [x * (size_chart["XS"] - size_chart[self.base_size]) for x in default_base_deltas],
                "S": [x * (size_chart["S"] - size_chart[self.base_size]) for x in default_base_deltas],
                "M": [x * (size_chart["M"] - size_chart[self.base_size]) for x in default_base_deltas],
                "L": [x * (size_chart["L"] - size_chart[self.base_size]) for x in default_base_deltas],
                "XL": [x * (size_chart["XL"] - size_chart[self.base_size]) for x in default_base_deltas]
            }
        )
        return deltas

    def override_deltas(self, measurement: str, size: str, new_delta: float):
        if size not in self.sizes.columns:
            logging.warn(f"Error: Size '{size}' is not a valid column.")
            return

        self.deltas = self.deltas.with_columns(
            pl.when(pl.col("Measurement") == measurement)
            .then(pl.lit(new_delta))
            .otherwise(pl.col(size))
            .alias(size)
        )

        # In case the delta that was changed was a base size's delta
        self.recalculate_deltas()

    def recalculate_deltas(self):
        numerical_deltas = self.deltas.select(pl.exclude("Measurement"))
        base_size_column = self.deltas.get_column(self.base_size)

        new_numerical_deltas = numerical_deltas - base_size_column
        final_deltas = pl.concat(
            [self.deltas.select("Measurement"), new_numerical_deltas],
            how="horizontal"
        )

        return final_deltas


    def _calculate_sizes(self):
        base_numeric = self.base.select(pl.exclude("Measurement"))
        deltas_numeric = self.deltas.select(pl.exclude("Measurement"))

        numeric_sizes = base_numeric + deltas_numeric

        final_sizes = pl.concat(
            [self.base.select("Measurement"), numeric_sizes],
            how="horizontal"
        )

        # Catch any negative (or 0) lengths:
        final_sizes = final_sizes.with_columns(
            pl.when(pl.selectors.numeric() > 0)
            .then(pl.selectors.numeric())
            .otherwise(pl.lit(None)))
        return final_sizes

    def validate_grading(self):
        size_order = ["XS", "S", "M", "L", "XL"]
        #numeric_sizes = self.sizes.select(size_order)

        # Create a list of expressions to calculate the difference between adjacent columns.
        # e.g., (pl.col("S") - pl.col("XS")), (pl.col("M") - pl.col("S")), ...
        diff_expressions = [
            (pl.col(size_order[i]) - pl.col(size_order[i - 1])).alias(f"diff_{size_order[i - 1]}_{size_order[i]}")
            for i in range(1, len(size_order))
        ]
        differences = self.sizes.select(diff_expressions)

        has_negative_grade = differences.select(
            pl.any_horizontal(cs.numeric() < 0)
        ).to_series().any()

        if has_negative_grade:
            logging.warn("\n--- GRADING VALIDATION WARNING ---\n Warning: A measurement decreases as the size gets larger.")

    def recalculate_measurement(self, measurement: str):
        '''
        This function essentially refreshes the value of a row in the table.
        '''
        fully_calculated_chart = self._calculate_sizes()
        correct_row = fully_calculated_chart.filter(
            pl.col("Measurement") == measurement
        )
        rows_to_keep = self.sizes.filter(
            pl.col("Measurement") != measurement
        )

        if correct_row.is_empty():
            logging.error(f"Error: Measurement '{measurement}' not found.")
            return

        # Order the results as in the original table
        measurement_order = self.base.get_column("Measurement").to_list()

        correct_row = correct_row.with_columns(
            pl.col("Measurement").cast(pl.Enum(categories=measurement_order))
        )
        rows_to_keep = rows_to_keep.with_columns(
            pl.col("Measurement").cast(pl.Enum(categories=measurement_order))
        )
        new_sizes = pl.concat([rows_to_keep, correct_row])
        self.sizes = new_sizes.sort("Measurement")
        self.sizes = new_sizes.with_columns(
            pl.col("Measurement").cast(pl.Enum(categories=measurement_order))
        ).sort("Measurement")

        self.validate_grading()

    def override(self, measurement: str, size: str, new_value: float):
        if size not in self.sizes.columns:
            logging.error(f"Error: Size '{size}' is not a valid column.")
            return
        if size == self.base_size:
            self.sizes = self.sizes.with_columns(
                pl.when(pl.col("Measurement") == measurement)
                .then(pl.lit(new_value))
                .otherwise(pl.col(size))
                .alias(size)
            )

            new_base_numeric = self.sizes.select(cs.numeric()) - self.deltas.select(cs.numeric())
            new_base_series = new_base_numeric.get_column(self.base_size)
            updated_base = self.base.select("Measurement")
            for col_name in self.deltas.select(cs.numeric()).columns:
                updated_base = updated_base.with_columns(new_base_series.alias(col_name))
            self.base = updated_base

            self.recalculate_measurement(measurement)


        else:
            current_base_value = self.sizes.filter(pl.col("Measurement") == measurement).select(self.base_size).item()
            new_delta = new_value - current_base_value

            self.override_deltas(measurement, size, new_delta)

            self.recalculate_measurement(measurement)

    def change_base_size(self, new_base_size):
        self.base_size = new_base_size
        self.deltas = self.recalculate_deltas()

    def save(self, type_of_garment):
        path = f"./{type_of_garment}"
        os.makedirs(path, exist_ok=True)

        config_data = {
            "base_size": self.base_size
        }

        self.base.write_csv(file=os.path.join(path, "base.csv"))
        self.deltas.write_csv(file=os.path.join(path, "deltas.csv"))
        with open(os.path.join(path, "config.json"), "w") as f:
            json.dump(config_data, f)

    @classmethod
    def load(cls, type_of_garment):
        path = f"./{type_of_garment}"

        base = pl.read_csv(os.path.join(path, "base.csv"))
        deltas = pl.read_csv(os.path.join(path, "deltas.csv"))

        with open(os.path.join(path, "config.json"), "r") as f:
            config_data = json.load(f)
        base_size = config_data["base_size"]

        # Create a garment object
        garment = cls(base_size=base_size)
        garment.base = base
        garment.deltas = deltas
        garment.sizes = garment._calculate_sizes()

        return garment

class Tshirt(Garment):
    def __init__(self, base_size="M"):
        tshirt_labels = ["Shoulder width", "Chest circumference", "Waist circumference", "Hip circumference"]
        tshirt_base_values = [46.0, 110.0, 102.0, 108.0]
        tshirt_delta_rules = [2.0, 4.0, 3.0, 3.0]

        super().__init__(
            measurement_labels=tshirt_labels,
            base_measurements=tshirt_base_values,
            default_deltas=tshirt_delta_rules,
            base_size=base_size
        )
