from fastapi import FastAPI, Query
import requests
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Coomer Proxy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SOURCE_URL = "https://coomer.st/api/v1/creators"
_cache = {"data": None}


@app.get("/creators")
def get_creators(
    q: str = Query("", description="Termo de busca (ex: nome do criador)"),
    service: str = Query("", description="Serviço (ex: onlyfans, fansly)"),
    sort_by: str = Query("favorited", description="Campo de ordenação"),
    order: str = Query("desc", description="Ordem (asc ou desc)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    favorited_min: int = Query(0, ge=0)
):
    """
    Retorna lista paginada de criadores, com busca por nome, filtro por serviço
    e ordenação personalizada.
    """

    # Buscar dados da API original, se não estiver no cache
    if _cache["data"] is None:
        print("Baixando dados da API pública...")
        headers = {"Accept": "text/css"}
        resp = requests.get(SOURCE_URL, headers=headers)
        if resp.status_code != 200:
            return {"error": f"Falha ao obter dados da API original ({resp.status_code})"}
        _cache["data"] = resp.json()

    data = _cache["data"]

    # --- FILTROS ---

    # Filtro por termo de busca (case-insensitive)
    if q:
        q_lower = q.lower()
        data = [
            item for item in data
            if q_lower in item.get("id", "").lower() or q_lower in item.get("name", "").lower()
        ]

    # Filtro por serviço (onlyfans, fansly etc)
    if service:
        service_lower = service.lower()
        data = [item for item in data if item.get("service", "").lower() == service_lower]

    # Filtro por número mínimo de favoritos
    data = [item for item in data if item.get("favorited", 0) >= favorited_min]

    # --- ORDENAÇÃO ---
    reverse_order = (order.lower() != "asc")
    if sort_by in ["favorited", "indexed", "updated"]:
        data = sorted(data, key=lambda x: x.get(sort_by, 0), reverse=reverse_order)

    # --- PAGINAÇÃO ---
    total = len(data)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = data[start:end]

    return {
        "query": q,
        "service": service,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "per_page": per_page,
        "total": total,
        "results": paginated
    }
