from fastapi import FastAPI, HTTPException, Request

from .data_processing import LeagueGameLogProcessing

app = FastAPI()

AVAILABLE_ENDPOINTS = {
    "leaguegamelog": LeagueGameLogProcessing,
}


@app.get("/api/{endpoint_name}")
async def get_endpoint_data(endpoint_name: str, request: Request):
    """Fetch data for the specified endpoint."""
    if endpoint_name not in AVAILABLE_ENDPOINTS:
        raise HTTPException(
            status_code=404, detail=f"Endpoint '{endpoint_name}' not found"
        )

    try:
        endpoint_class = AVAILABLE_ENDPOINTS[endpoint_name]
        params = dict(request.query_params)
        endpoint = endpoint_class(**params)

        return endpoint.get_json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

def main():
    """Run the FastAPI server using Uvicorn."""
    import uvicorn
    uvicorn.run("src.api.server:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
