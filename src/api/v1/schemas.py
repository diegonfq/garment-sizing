from pydantic import BaseModel, Field
from typing import Dict, Literal, Optional


SizeType = Literal["XS", "S", "M", "L", "XL"]

# Schema for creating a garment; data required in a POST request
class GarmentCreate(BaseModel):
    garment_type: str = Field(
        ...,
        examples=["tshirt", "jeans"],
        description="A specific name for the garment model."
    )
    base_size: str = Field(
        "M",
        examples=["S", "M"],
        description="The base size from which other sizes are graded."
    )
    measurements: Dict[str, float] = Field(
        ...,
        examples=[{"Shoulder width": 46.0, "Chest circumference": 110.0}],
        description="A dictionary of base measurement names and their values."
    )
    deltas: Dict[str, Dict[SizeType, float]] = Field(
        ...,
        examples=[{
            "Shoulder width": {"XS": -4.0, "S": -2.0, "M": 0.0, "L": 2.0, "XL": 4.0},
            "Chest circumference": {"XS": -8.0, "S": -4.0, "M": 0.0, "L": 4.0, "XL": 8.0}
        }],
        description="A nested dictionary defining the grade rules (deltas) for each measurement and size."
    )

# Schema for reading a Garment, displaying only the basic info (e.g. in list view)
# in response to a GET request (eg GET /garments/list)
class GarmentReadBasic(BaseModel):
    id: int
    garment_type: str
    base_size: SizeType

    class Config:
        from_attributes = True

# Schema for reading a full garment, in response to a GET request
# (e.g. GET /garments/{id}). Inherits from GarmentReadBasic and adds the tables
class GarmentFullSpec(GarmentReadBasic):
    sizes: Dict[str, Dict[SizeType, Optional[float]]]
    deltas: Dict[str, Dict[SizeType, float]]