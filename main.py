import httpx
from fastapi import FastAPI, Request, Response, status

app = FastAPI()


DEFAULT_SERVER_URL = "https://shiftsayan--tough-server-fastapi-app.modal.run/completion"


@app.post("/completion")
async def completion_endpoint(request: Request):
    data = await request.json()

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(DEFAULT_SERVER_URL, json=data)

            return Response(
                content=resp.content,
                status_code=resp.status_code,
                media_type=resp.headers.get("content-type"),
            )
        except httpx.HTTPError as e:
            return Response(
                content=f"Upstream request failed: {e}",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            return Response(
                content=f"Unexpected error: {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
