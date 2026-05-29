"""
coletor.py
Coleta vagas da Adzuna API e Jooble API.
"""
import os
import time
import requests
from dotenv import load_dotenv
from normalizador import normalizar_adzuna, normalizar_jooble, remover_duplicatas, CATEGORIA_MAP

load_dotenv()

ADZUNA_ID  = os.getenv("ADZUNA_APP_ID")
ADZUNA_KEY = os.getenv("ADZUNA_APP_KEY")
JOOBLE_KEY = os.getenv("JOOBLE_KEY")

# Categorias a buscar — tag Adzuna + query Jooble + categoria normalizada
BUSCAS = [
    ("it-jobs",                       "desenvolvedor programador",  "Tecnologia"),
    ("engineering-jobs",              "engenheiro engenharia",      "Tecnologia"),
    ("scientific-qa-jobs",            "cientista dados pesquisa",   "Tecnologia"),
    ("creative-design-jobs",          "designer ux ui",             "Tecnologia"),
    ("healthcare-nursing-jobs",       "medico enfermeiro saude",    "Saúde"),
    ("teaching-jobs",                 "professor educacao ensino",  "Educação"),
    ("legal-jobs",                    "advogado juridico direito",  "Jurídico"),
    ("accounting-finance-jobs",       "contador financeiro",        "Administrativo"),
    ("admin-jobs",                    "administrativo assistente",  "Administrativo"),
    ("hr-jobs",                       "recursos humanos rh",        "Administrativo"),
    ("pr-advertising-marketing-jobs", "marketing publicidade",      "Administrativo"),
    ("logistics-warehouse-jobs",      "logistica estoque",          "Industrial"),
    ("trade-construction-jobs",       "construcao civil obras",     "Industrial"),
    ("manufacturing-jobs",            "producao industrial fabrica","Industrial"),
]


def coletar_adzuna(tag: str, paginas: int = 3) -> list[dict]:
    """Coleta vagas da Adzuna por categoria."""
    vagas = []
    for pagina in range(1, paginas + 1):
        try:
            url = (
                f"https://api.adzuna.com/v1/api/jobs/br/search/{pagina}"
                f"?app_id={ADZUNA_ID}&app_key={ADZUNA_KEY}"
                f"&results_per_page=50&category={tag}"
                f"&content-type=application/json"
            )
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            data = r.json()
            resultados = data.get("results", [])
            if not resultados:
                break
            vagas.extend(resultados)
            print(f"    Adzuna [{tag}] página {pagina}: {len(resultados)} vagas")
            time.sleep(0.5)  # respeita rate limit
        except Exception as e:
            print(f"    ❌ Adzuna [{tag}] p{pagina}: {e}")
            break
    return vagas


def coletar_jooble(query: str, paginas: int = 3) -> list[dict]:
    """Coleta vagas da Jooble por query."""
    vagas = []
    for pagina in range(1, paginas + 1):
        try:
            url  = f"https://jooble.org/api/{JOOBLE_KEY}"
            body = {
                "keywords": query,
                "location": "Brasil",
                "page": str(pagina),
                "ResultOnPage": 50,
            }
            r = requests.post(url, json=body, timeout=15)
            r.raise_for_status()
            data = r.json()
            jobs = data.get("jobs", [])
            if not jobs:
                break
            vagas.extend(jobs)
            print(f"    Jooble [{query[:30]}] página {pagina}: {len(jobs)} vagas")
            time.sleep(0.5)
        except Exception as e:
            print(f"    ❌ Jooble [{query[:30]}] p{pagina}: {e}")
            break
    return vagas


def coletar_tudo() -> list[dict]:
    """Coleta e normaliza todas as categorias das duas APIs."""
    todas = []

    for tag_adzuna, query_jooble, categoria in BUSCAS:
        print(f"\n📂 {categoria} — {tag_adzuna}")

        # Adzuna
        brutos_adzuna = coletar_adzuna(tag_adzuna)
        norm_adzuna   = [normalizar_adzuna(v) for v in brutos_adzuna]

        # Jooble (desativada temporariamente — erro 403)
        norm_jooble = []

        combinadas = remover_duplicatas(norm_adzuna + norm_jooble)
        print(f"  ✅ {len(norm_adzuna)} Adzuna + {len(norm_jooble)} Jooble = {len(combinadas)} únicas")
        todas.extend(combinadas)

    todas = remover_duplicatas(todas)
    print(f"\n🎯 Total final: {len(todas)} vagas únicas coletadas")
    return todas


if __name__ == "__main__":
    vagas = coletar_tudo()
    print(f"\nPrimeira vaga normalizada:")
    if vagas:
        for k, v in vagas[0].items():
            print(f"  {k}: {v}")
