from fastapi import APIRouter, HTTPException

from app.models.data import DataCreate, DataUpdate
from app.services import data_service


router = APIRouter(
    prefix="/api/data",
    tags=["Data"],
)


@router.post("")
def create_data(data: DataCreate):
    try:
        return data_service.create_data(data)

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )


@router.get("")
def get_data():
    return data_service.get_all_data()


@router.get("/summary")
def get_summary():
    return data_service.get_summary()


@router.put("/{document_id}")
def update_data(
    document_id: str,
    data: DataUpdate,
):
    try:
        return data_service.update_data(
            document_id,
            data,
        )

    except LookupError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.delete("/{document_id}")
def delete_data(document_id: str):
    try:
        return data_service.delete_data(document_id)

    except LookupError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )