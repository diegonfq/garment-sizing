from pydantic import BaseModel, Field
from typing import Dict, Literal, Optional, List


SizeType = Literal["XS", "S", "M", "L", "XL"]


class GarmentCreate(BaseModel):
    '''
    Schema for creating a garment; data required in a POST request
    '''
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
    sizes_to_order: List[str] = Field(
        ...,
        examples=[["S","M","L"]],
        description="A list of sizes which are pending order"
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

class GarmentReadBasic(BaseModel):
    '''
    Schema for reading a Garment, displaying only the basic info (e.g. in list view)
    in response to a GET request (eg GET /garments/list)
    '''
    id: int
    garment_type: str
    base_size: SizeType

    class Config:
        from_attributes = True

class GarmentFullSpec(GarmentReadBasic):
    '''
    Schema for reading a full garment, in response to a GET request
    (e.g. GET /garments/{id}). Inherits from GarmentReadBasic and adds the tables
    '''
    sizes: Dict[str, Dict[SizeType, Optional[float]]]
    deltas: Dict[str, Dict[SizeType, float]]

class GarmentUpdate(BaseModel):
    """
    Pydantic model for PATCH requests. All fields are optional.
    """
    garment_type: Optional[str] = Field(
        default=None,
        examples=["tshirt", "jeans"],
        description="A specific name for the garment model."
    )
    base_size: Optional[str] = Field(
        default=None,
        examples=["S", "M"],
        description="The base size from which other sizes are graded."
    )
    sizes_to_order: Optional[List[str]] = Field(
        default=None,
        examples=[["S", "M", "L"]],
        description="A list of sizes which are pending order"
    )