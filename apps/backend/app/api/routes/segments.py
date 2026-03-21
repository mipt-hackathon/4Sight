from fastapi import APIRouter

router = APIRouter()


@router.get("/segments")
def list_segments() -> dict:
    # TODO: Replace with segmentation outputs sourced from mart/serving layers.
    return {
        "status": "stub",
        "segments": [],
        "todo": "Implement RFM/cohort/ABC-XYZ segment listing endpoint.",
    }
