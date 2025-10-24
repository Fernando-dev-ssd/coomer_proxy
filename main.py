from fastapi import FastAPI, Query
import requests
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

app = FastAPI(title="Coomer Proxy API")

# Libera CORS pro Flutter
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# URL base da API pública
SOURCE_URL = "https://coomer.st/api/v1/creators"

# Cache simples (evita bater sempre na API)
_cache = {"data": None}


@app.get("/creators")
def get_creators(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    favorited_min: int = Query(0, ge=0)
):
    """
    Retorna lista paginada de criadores, ordenada por 'favorited' desc
    e filtrada por favorited >= favorited_min.
    """

    # Busca dados se o cache estiver vazio
    if _cache["data"] is None:
        print("Baixando dados da API pública...")
        headers = {"Accept": "text/css"}
        resp = requests.get(SOURCE_URL, headers=headers)
        if resp.status_code != 200:
            return {"error": f"Falha ao obter dados da API original ({resp.status_code})"}
        _cache["data"] = resp.json()

    data = _cache["data"]

    # Filtra
    filtered = [item for item in data if item.get("favorited", 0) >= favorited_min]

    # Ordena
    sorted_data = sorted(filtered, key=lambda x: x.get("favorited", 0), reverse=True)

    # Paginação
    start = (page - 1) * per_page
    end = start + per_page
    paginated = sorted_data[start:end]

    return {
        "page": page,
        "per_page": per_page,
        "total": len(sorted_data),
        "results": paginated
    }



@app.get("/refresh")
def refresh_cache():
    """Força atualizar os dados do cache."""
    global _cache
    resp = requests.get(SOURCE_URL)
    if resp.status_code == 200:
        _cache["data"] = resp.json()
        return {"status": "Cache atualizado"}
    return {"error": "Falha ao atualizar cache"}


@app.get("/")
def root():
    return {"status": "ok", "message": "Coomer Proxy API ativa"}

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return PlainTextResponse("", status_code=204)