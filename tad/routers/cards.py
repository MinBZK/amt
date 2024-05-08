from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(
    prefix="/cards",
    tags=["cards"],
)


@router.get("/")
async def test():
    return [{"username": "Rick"}, {"username": "Morty"}]


@router.post("/move", response_class=HTMLResponse)
async def moved_card(request: Request):
    json = await request.json()
    response = "<div>JSON received data: " + str(json) + "</div>"
    return response
