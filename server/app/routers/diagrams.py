from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.diagrams import generators
from app.models.user import User

router = APIRouter(prefix="/diagrams", tags=["diagrams"])


class DiagramResponse(BaseModel):
    name: str
    format: str
    content: str
    description: str


@router.get("/{diagram_name}", response_model=DiagramResponse)
def get_diagram(
    diagram_name: str,
    format: str = "ascii",
    _: User = Depends(get_current_user),
):
    if diagram_name not in generators.GENERATORS:
        raise HTTPException(status_code=404, detail="Unknown diagram. Use architecture, er or ai-workflow")
    if format not in ("ascii", "svg"):
        raise HTTPException(status_code=400, detail="format must be 'ascii' or 'svg'")
    result = generators.GENERATORS[diagram_name]()
    return DiagramResponse(
        name=result["name"],
        format=format,
        content=result[format],
        description=result["description"],
    )
