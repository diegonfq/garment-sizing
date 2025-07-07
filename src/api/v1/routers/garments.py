from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, dependencies
from src.core.domain.garment import Garment
import src.core.domain.exceptions as exceptions
from src.core.domain.models import Garment as GarmentModel

router = APIRouter()

@router.get("/")
def read_root():
    return {"Hola": "Mundo"}

@router.post("/garments/", response_model=schemas.GarmentReadBasic, status_code=201)
def create_garment(garment_data: schemas.GarmentCreate, db: Session = Depends(dependencies.get_db)):
    garment_type = garment_data.garment_type.lower()


    try:
        new_garment_id = Garment.create_new_garment(
            db_session=db,
            garment_type=garment_type,
            base_size=garment_data.base_size,
            measurements=garment_data.measurements,
            deltas=garment_data.deltas
        )
    except exceptions.DuplicateGarmentError as e:
        raise HTTPException(status_code=404, detail=str(e))

    db_garment = db.query(GarmentModel).filter(GarmentModel.id == new_garment_id).one()
    return db_garment

@router.get("/garments/", response_model=List[schemas.GarmentReadBasic])
def read_garment_list(db: Session = Depends(dependencies.get_db)):
    return db.query(GarmentModel).order_by(GarmentModel.id).all()

@router.get("/garments/{garment_id}")
def read_garment_spec(garment_id: int, db: Session = Depends(dependencies.get_db)):
    match = db.query(GarmentModel).filter(GarmentModel.id == garment_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Item not found")

    garment_engine = Garment(db, garment_id)
    sizes_list_of_dicts = garment_engine.sizes.to_dicts()
    deltas_list_of_dicts = garment_engine.deltas.to_dicts()

    sizes_dict = {row['Measurement']: {k: v for k, v in row.items() if k != 'Measurement'} for row in sizes_list_of_dicts}
    deltas_dict = {row['Measurement']: {k: v for k, v in row.items() if k != 'Measurement'} for row in deltas_list_of_dicts}

    response = schemas.GarmentFullSpec(
        id=garment_engine.garment_model.id,
        garment_type=garment_engine.garment_model.garment_type,
        base_size=garment_engine.garment_model.base_size,
        sizes=sizes_dict,
        deltas=deltas_dict
    )
    return response

@router.delete("/garments/{garment_id}", status_code=204)
def remove_garment(garment_id: int, db: Session = Depends(dependencies.get_db)):
    try:
        Garment.remove_garment(db, garment_id)
    except exceptions.GarmentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return

@router.get("/admin/")
def access_admin():
    raise HTTPException(status_code=401, detail="No admin privileges")

@router.get("/oldresource/")
def read_old_resource():
    raise HTTPException(status_code=410, detail="Resource no longer exists")

@router.get("/illegal/")
def open_illegal():
    raise HTTPException(status_code=451, detail="Content unavailable in your region")