"""
normalizador.py
Transforma respostas brutas da Adzuna e Jooble num formato unificado.
"""
from datetime import datetime, timezone
import re


# ─── Mapeamento de categorias ────────────────────────────

CATEGORIA_MAP = {
    "it-jobs":                       "Tecnologia",
    "engineering-jobs":              "Tecnologia",
    "scientific-qa-jobs":            "Tecnologia",
    "creative-design-jobs":          "Tecnologia",
    "healthcare-nursing-jobs":       "Saúde",
    "teaching-jobs":                 "Educação",
    "legal-jobs":                    "Jurídico",
    "accounting-finance-jobs":       "Administrativo",
    "admin-jobs":                    "Administrativo",
    "hr-jobs":                       "Administrativo",
    "pr-advertising-marketing-jobs": "Administrativo",
    "consultancy-jobs":              "Administrativo",
    "sales-jobs":                    "Administrativo",
    "logistics-warehouse-jobs":      "Industrial",
    "trade-construction-jobs":       "Industrial",
    "manufacturing-jobs":            "Industrial",
    "energy-oil-gas-jobs":           "Industrial",
    "maintenance-jobs":              "Industrial",
    "customer-services-jobs":        "Outros",
    "retail-jobs":                   "Outros",
    "hospitality-catering-jobs":     "Outros",
    "travel-jobs":                   "Outros",
    "social-work-jobs":              "Outros",
    "other-general-jobs":            "Outros",
}

HARD_SKILLS = [
    "python", "sql", "aws", "react", "java", "node.js", "docker",
    "kubernetes", "typescript", "power bi", "azure", "gcp", "spark",
    "dbt", "airflow", "tableau", "git", "javascript", "c#", "go",
    "terraform", "kafka", "mongodb", "postgresql", "fastapi", "excel",
    "linux", "tensorflow", "pytorch", "scikit-learn", "pandas",
    "machine learning", "deep learning", "data science",
]

SOFT_SKILLS = [
    "comunicação", "liderança", "trabalho em equipe", "proatividade",
    "organização", "criatividade", "resolução de problemas", "flexibilidade",
    "gestão de tempo", "relacionamento interpessoal", "pensamento crítico",
    "adaptabilidade", "negociação", "empatia", "colaboração",
    "communication", "leadership", "teamwork", "problem solving",
    "time management", "critical thinking", "adaptability",
]

ESTADOS_BR = {
    "acre": "AC", "alagoas": "AL", "amapá": "AP", "amazonas": "AM",
    "bahia": "BA", "ceará": "CE", "distrito federal": "DF",
    "espírito santo": "ES", "goiás": "GO", "maranhão": "MA",
    "mato grosso": "MT", "mato grosso do sul": "MS", "minas gerais": "MG",
    "pará": "PA", "paraíba": "PB", "paraná": "PR", "pernambuco": "PE",
    "piauí": "PI", "rio de janeiro": "RJ", "rio grande do norte": "RN",
    "rio grande do sul": "RS", "rondônia": "RO", "roraima": "RR",
    "santa catarina": "SC", "são paulo": "SP", "sergipe": "SE",
    "tocantins": "TO",
    "ac":"AC","al":"AL","ap":"AP","am":"AM","ba":"BA","ce":"CE",
    "df":"DF","es":"ES","go":"GO","ma":"MA","mt":"MT","ms":"MS",
    "mg":"MG","pa":"PA","pb":"PB","pr":"PR","pe":"PE","pi":"PI",
    "rj":"RJ","rn":"RN","rs":"RS","ro":"RO","rr":"RR","sc":"SC",
    "sp":"SP","se":"SE","to":"TO",
}

REGIOES = {
    "AC":"Norte","AM":"Norte","AP":"Norte","PA":"Norte","RO":"Norte","RR":"Norte","TO":"Norte",
    "AL":"Nordeste","BA":"Nordeste","CE":"Nordeste","MA":"Nordeste","PB":"Nordeste",
    "PE":"Nordeste","PI":"Nordeste","RN":"Nordeste","SE":"Nordeste",
    "DF":"Centro-Oeste","GO":"Centro-Oeste","MS":"Centro-Oeste","MT":"Centro-Oeste",
    "ES":"Sudeste","MG":"Sudeste","RJ":"Sudeste","SP":"Sudeste",
    "PR":"Sul","RS":"Sul","SC":"Sul",
}

# ─── Mapeamento cidade/bairro → (cidade_canônica, estado) ────────────────────
# Cobre todas as localidades problemáticas encontradas nos dados coletados.
# Bairros de SP são mapeados para "São Paulo".
# Cidades do interior são mapeadas para seu estado correto.

CIDADE_PARA_ESTADO: dict[str, tuple[str, str]] = {
    # ── Bairros / distritos de São Paulo (SP) ──
    "jardim peri":            ("São Paulo", "SP"),
    "vila marari":            ("São Paulo", "SP"),
    "mandaqui":               ("São Paulo", "SP"),
    "brás":                   ("São Paulo", "SP"),
    "bras":                   ("São Paulo", "SP"),
    "jardim europa":          ("São Paulo", "SP"),
    "vila lageado":           ("São Paulo", "SP"),
    "jardim glória":          ("São Paulo", "SP"),
    "jardim gloria":          ("São Paulo", "SP"),
    "chácara cruzeiro do sul":("São Paulo", "SP"),
    "chacara cruzeiro do sul":("São Paulo", "SP"),
    "vila clementino":        ("São Paulo", "SP"),
    "lourdes":                ("São Paulo", "SP"),  # bairro SP (também BH, mas SP mais comum na Adzuna)
    "bauru": ("Bauru", "SP"),
    "itaquaquecetuba": ("Itaquaquecetuba", "SP"),
    "cajamar": ("Cajamar", "SP"),
    "jandira": ("Jandira", "SP"),
    "americana": ("Americana", "SP"),
    "santana de parnaíba": ("Santana de Parnaíba", "SP"),
    "rio claro": ("Rio Claro", "SP"),
    "guaratinguetá": ("Guaratinguetá", "SP"),
    "jau": ("Jaú", "SP"),
    "jaú": ("Jaú", "SP"),
    "atibaia": ("Atibaia", "SP"),
    "taubaté": ("Taubaté", "SP"),
    "taubate": ("Taubaté", "SP"),
    "itu": ("Itu", "SP"),
    "presidente prudente": ("Presidente Prudente", "SP"),
    "arujá": ("Arujá", "SP"),
    "aruja": ("Arujá", "SP"),
    "campo limpo paulista": ("Campo Limpo Paulista", "SP"),
    "salto": ("Salto", "SP"),
    "nova odessa": ("Nova Odessa", "SP"),
    "monte mor": ("Monte Mor", "SP"),
    "mairinque": ("Mairinque", "SP"),
    "consolação": ("São Paulo", "SP"),
    "consolacao": ("São Paulo", "SP"),
    "itaim bibi": ("São Paulo", "SP"),
    "vila carrão": ("São Paulo", "SP"),
    "vila carrao": ("São Paulo", "SP"),
    "higienópolis": ("São Paulo", "SP"),
    "higienopolis": ("São Paulo", "SP"),
    "jardim paulistano": ("São Paulo", "SP"),

    # ── Bairros / localidades do Rio de Janeiro ──
    "guarapes":               ("Rio de Janeiro", "RJ"),
    "jardim panorama":        ("Rio de Janeiro", "RJ"),  # localidade genérica → RJ

    # ── Bairros / distritos de João Pessoa (PB) ──
    "jardim humaitá":         ("João Pessoa", "PB"),
    "jardim humaitá":         ("João Pessoa", "PB"),
    "jardim america":         ("João Pessoa", "PB"),
    "jardim américa":         ("João Pessoa", "PB"),

    # ── Bairros de Santos (SP) ──
    "mangabeiras":            ("Santos", "SP"),   # bairro de Santos

    # ── Cidades do interior de SP ──
    "santos":                 ("Santos", "SP"),
    "barueri":                ("Barueri", "SP"),
    "campinas":               ("Campinas", "SP"),
    "araçariguama":           ("Araçariguama", "SP"),
    "aracariguama":           ("Araçariguama", "SP"),
    "são bernardo do campo":  ("São Bernardo do Campo", "SP"),
    "sao bernardo do campo":  ("São Bernardo do Campo", "SP"),
    "são bernado do campos":  ("São Bernardo do Campo", "SP"),
    "sao bernado do campos":  ("São Bernardo do Campo", "SP"),
    "sorocaba":               ("Sorocaba", "SP"),
    "valinhos":               ("Valinhos", "SP"),
    "santo andré":            ("Santo André", "SP"),
    "santo andre":            ("Santo André", "SP"),
    "franco da rocha":        ("Franco da Rocha", "SP"),
    "franca":                 ("Franca", "SP"),
    "diadema":                ("Diadema", "SP"),
    "indaiatuba":             ("Indaiatuba", "SP"),
    "taboão da serra":        ("Taboão da Serra", "SP"),
    "taboao da serra":        ("Taboão da Serra", "SP"),
    "guarulhos":              ("Guarulhos", "SP"),
    "jacareí":                ("Jacareí", "SP"),
    "jacarei":                ("Jacareí", "SP"),
    "osasco":                 ("Osasco", "SP"),
    "mauá":                   ("Mauá", "SP"),
    "maua":                   ("Mauá", "SP"),
    "mogi guaçu":             ("Mogi Guaçu", "SP"),
    "mogi guacu":             ("Mogi Guaçu", "SP"),
    "jundiaí":                ("Jundiaí", "SP"),
    "jundiai":                ("Jundiaí", "SP"),
    "jaguariúna":             ("Jaguariúna", "SP"),
    "jaguariuna":             ("Jaguariúna", "SP"),
    "cotia":                  ("Cotia", "SP"),
    "engenheiro coelho":      ("Engenheiro Coelho", "SP"),
    "cravinhos":              ("Cravinhos", "SP"),
    "cachoeira paulista":     ("Cachoeira Paulista", "SP"),
    "são roque":              ("São Roque", "SP"),
    "sao roque":              ("São Roque", "SP"),
    "várzea paulista":        ("Várzea Paulista", "SP"),
    "varzea paulista":        ("Várzea Paulista", "SP"),
    "barra bonita":           ("Barra Bonita", "SP"),
    "vinhedo":                ("Vinhedo", "SP"),
    "pirassununga":           ("Pirassununga", "SP"),
    "são gerardo":            ("São Paulo", "SP"),   # bairro/distrito SP
    "sao gerardo":            ("São Paulo", "SP"),
    "praia grande":           ("Praia Grande", "SP"),
    "hortolândia":            ("Hortolândia", "SP"),
    "hortolandia":            ("Hortolândia", "SP"),
    "suzano":                 ("Suzano", "SP"),
    "suzana":                 ("Suzano", "SP"),       # grafia alternativa
    "charqueada":             ("Charqueada", "SP"),
    "botucatu":               ("Botucatu", "SP"),
    "paulínia":               ("Paulínia", "SP"),
    "paulinia":               ("Paulínia", "SP"),
    "ribeirão preto":         ("Ribeirão Preto", "SP"),
    "ribeirao preto":         ("Ribeirão Preto", "SP"),
    "sumaré":                 ("Sumaré", "SP"),
    "sumare":                 ("Sumaré", "SP"),
    "itapecerica da serra":   ("Itapecerica da Serra", "SP"),
    "guarujá":                ("Guarujá", "SP"),
    "guaruja":                ("Guarujá", "SP"),
    "araras":                 ("Araras", "SP"),
    "são josé dos campos":    ("São José dos Campos", "SP"),
    "sao jose dos campos":    ("São José dos Campos", "SP"),
    "embu-guaçu":             ("Embu-Guaçu", "SP"),
    "embu guacu":             ("Embu-Guaçu", "SP"),
    "são josé do rio preto":  ("São José do Rio Preto", "SP"),
    "sao jose do rio preto":  ("São José do Rio Preto", "SP"),
    "porto feliz":            ("Porto Feliz", "SP"),
    "jaboticabal":            ("Jaboticabal", "SP"),
    "jaboticabai":            ("Jaboticabal", "SP"),  # typo da API
    "salto de pirapora":      ("Salto de Pirapora", "SP"),
    "piracicaba":             ("Piracicaba", "SP"),
    "lins":                   ("Lins", "SP"),
    "limeira":                ("Limeira", "SP"),
    "ferraz de vasconcelos":  ("Ferraz de Vasconcelos", "SP"),
    "são carlos":             ("São Carlos", "SP"),
    "sao carlos":             ("São Carlos", "SP"),
    "barretos":               ("Barretos", "SP"),
    "bebedouro":              ("Bebedouro", "SP"),
    "fernandópolis":          ("Fernandópolis", "SP"),
    "fernadópolis":           ("Fernandópolis", "SP"),  # typo da API
    "fernadopolis":           ("Fernandópolis", "SP"),
    "bragança paulista":      ("Bragança Paulista", "SP"),
    "braganca paulista":      ("Bragança Paulista", "SP"),
    "mogi das cruzes":        ("Mogi das Cruzes", "SP"),
    "itapetininga":           ("Itapetininga", "SP"),
    "ribeirão pires":         ("Ribeirão Pires", "SP"),
    "ribeirao pires":         ("Ribeirão Pires", "SP"),
    "são caetano do sul":     ("São Caetano do Sul", "SP"),
    "sao caetano do sul":     ("São Caetano do Sul", "SP"),
    "amparo":                 ("Amparo", "SP"),
    "holambra":               ("Holambra", "SP"),
    "várzea paulista":        ("Várzea Paulista", "SP"),

    # ── Cidades do Rio de Janeiro ──
    "volta redonda":          ("Volta Redonda", "RJ"),
    "macaé":                  ("Macaé", "RJ"),
    "macae":                  ("Macaé", "RJ"),
    "nova friburgo":          ("Nova Friburgo", "RJ"),
    "arraial do cabo":        ("Arraial do Cabo", "RJ"),
    "niterói":                ("Niterói", "RJ"),
    "niteroi":                ("Niterói", "RJ"),
    "duque de caxias":        ("Duque de Caxias", "RJ"),
    "são joão de meriti":     ("São João de Meriti", "RJ"),
    "sao joao de meriti":     ("São João de Meriti", "RJ"),
    "barra mansa":            ("Barra Mansa", "RJ"),
    "são gonçalo":            ("São Gonçalo", "RJ"),
    "sao goncalo":            ("São Gonçalo", "RJ"),
    "nova iguaçu":            ("Nova Iguaçu", "RJ"),
    "nova iguacu":            ("Nova Iguaçu", "RJ"),
    "nilópolis":              ("Nilópolis", "RJ"),
    "nilopolis":              ("Nilópolis", "RJ"),
    "teresópolis":            ("Teresópolis", "RJ"),
    "teresopolis":            ("Teresópolis", "RJ"),
    "petrópolis":             ("Petrópolis", "RJ"),
    "petropolis":             ("Petrópolis", "RJ"),
    "campos dos goytacazes":  ("Campos dos Goytacazes", "RJ"),
    "campos do goytacazes":   ("Campos dos Goytacazes", "RJ"),
    "três rios":              ("Três Rios", "RJ"),
    "tres rios":              ("Três Rios", "RJ"),
    "armação dos búzios":     ("Armação dos Búzios", "RJ"),
    "armacao dos buzios":     ("Armação dos Búzios", "RJ"),
    "poá":                    ("Poá", "SP"),   # Poá é SP, não RJ
    "poa":                    ("Poá", "SP"),

    # ── Cidades do Espírito Santo ──
    "vitória":                ("Vitória", "ES"),
    "vitoria":                ("Vitória", "ES"),
    "linhares":               ("Linhares", "ES"),
    "cariacica":              ("Cariacica", "ES"),
    "colatina":               ("Colatina", "ES"),
    "vila velha":             ("Vila Velha", "ES"),
    "serra":                  ("Serra", "ES"),
    "santa teresa":           ("Santa Teresa", "ES"),


    # ── Cidades da Paraíba ──
    "joão pessoa":            ("João Pessoa", "PB"),
    "joao pessoa":            ("João Pessoa", "PB"),
    "manuel sátiro":          ("João Pessoa", "PB"),  # bairro de JP
    "manuel satiro":          ("João Pessoa", "PB"),

    # ── Cidades de MG ──
    "marília":                ("Marília", "SP"),  # Marília é SP
    "marilia":                ("Marília", "SP"),

    # ── Cidades de SP (São Vicente) ──
    "são vicente":            ("São Vicente", "SP"),
    "sao vicente":            ("São Vicente", "SP"),
    "são vincente":           ("São Vicente", "SP"),  # typo da API

    # ── Rio Grande do Norte ──
    "são pedro da aldeia":    ("São Pedro da Aldeia", "RJ"),  # é RJ
    "sao pedro da aldeia":    ("São Pedro da Aldeia", "RJ"),

    # ── Resende (typo da API: "Resente") ──
    "resende":                ("Resende", "RJ"),
    "resente":                ("Resende", "RJ"),

    # ── Brasil ─
    "brasil": ("Brasil", "BR"),

    # ── Outros bairros ──
    "cidade dos funcionários": ("Fortaleza", "CE"),
    "cidade dos funcionarios": ("Fortaleza", "CE"),
    "caminho das árvores": ("Salvador", "BA"),
    "caminho das arvores": ("Salvador", "BA"),
    "conjunto confisco": ("Belo Horizonte", "MG"),
    "rodolfo teófilo": ("Fortaleza", "CE"),
    "rodolfo teofilo": ("Fortaleza", "CE"),

    # ── Estados vindo como cidade ──
    "espirito santo": ("Vitória", "ES"),
    "espírito santo": ("Vitória", "ES"),

    # ── Novos casos encontrados ──
    "caieiras": ("Caieiras", "SP"),
    "araçatuba": ("Araçatuba", "SP"),
    "aracatuba": ("Araçatuba", "SP"),
    "itupeva": ("Itupeva", "SP"),
    "louveira": ("Louveira", "SP"),
    "carapicuíba": ("Carapicuíba", "SP"),
    "carapicuiba": ("Carapicuíba", "SP"),
    "caçapava": ("Caçapava", "SP"),
    "cacapava": ("Caçapava", "SP"),
    "teresina": ("Teresina", "PI"),
    "campina grande": ("Campina Grande", "PB"),
    "cabreúva": ("Cabreúva", "SP"),
    "cabreuva": ("Cabreúva", "SP"),
    "sertãozinho": ("Sertãozinho", "SP"),
    "sertaozinho": ("Sertãozinho", "SP"),
    "francisco morato": ("Francisco Morato", "SP"),
    "votorantim": ("Votorantim", "SP"),
    "itapeva": ("Itapeva", "SP"),
    "araraquara": ("Araraquara", "SP"),
    "vargem grande paulista": ("Vargem Grande Paulista", "SP"),
    "orlândia": ("Orlândia", "SP"),
    "orlandia": ("Orlândia", "SP"),
    "avaré": ("Avaré", "SP"),
    "avare": ("Avaré", "SP"),
    "iracemápolis": ("Iracemápolis", "SP"),
    "iracemapolis": ("Iracemápolis", "SP"),
    "capivari": ("Capivari", "SP"),
    "itapevi": ("Itapevi", "SP"),
    "araçoiaba da serra": ("Araçoiaba da Serra", "SP"),
    "aracoiaba da serra": ("Araçoiaba da Serra", "SP"),
    "boituva": ("Boituva", "SP"),
    "catanduva": ("Catanduva", "SP"),
    "mairiporã": ("Mairiporã", "SP"),
    "mairipora": ("Mairiporã", "SP"),
    "pariquera-açu": ("Pariquera-Açu", "SP"),
    "pariquera-acu": ("Pariquera-Açu", "SP"),
    "itatiba": ("Itatiba", "SP"),
    "embu": ("Embu das Artes", "SP"),
    "tupi paulista": ("Tupi Paulista", "SP"),
    "monte aprazível": ("Monte Aprazível", "SP"),
    "monte aprazivel": ("Monte Aprazível", "SP"),
    "mococa": ("Mococa", "SP"),
    "santa bárbara d'oeste": ("Santa Bárbara d'Oeste", "SP"),
    "santa barbara d'oeste": ("Santa Bárbara d'Oeste", "SP"),
    "capão bonito": ("Capão Bonito", "SP"),
    "capao bonito": ("Capão Bonito", "SP"),
    "iperó": ("Iperó", "SP"),
    "ipero": ("Iperó", "SP"),
    "jardinópolis": ("Jardinópolis", "SP"),
    "jardinopolis": ("Jardinópolis", "SP"),
    "osvaldo cruz": ("Osvaldo Cruz", "SP"),
    "tietê": ("Tietê", "SP"),
    "tiete": ("Tietê", "SP"),
    "santa isabel": ("Santa Isabel", "SP"),
    "bady bassitt": ("Bady Bassitt", "SP"),
    "jarinu": ("Jarinu", "SP"),

    # ── RJ ──
    "itaperuna": ("Itaperuna", "RJ"),
    "rio das ostras": ("Rio das Ostras", "RJ"),
    "queimados": ("Queimados", "RJ"),
    "itaboraí": ("Itaboraí", "RJ"),
    "itaborai": ("Itaboraí", "RJ"),
    "cabo frio": ("Cabo Frio", "RJ"),
    "maricá": ("Maricá", "RJ"),
    "marica": ("Maricá", "RJ"),
    "penedo": ("Itatiaia", "RJ"),

    # ── MG ──
    "uberaba": ("Uberaba", "MG"),
    "funcionários": ("Belo Horizonte", "MG"),
    "funcionarios": ("Belo Horizonte", "MG"),

    # ── RR ──
    "boa vista": ("Boa Vista", "RR"),

    # ── CE ──
    "curió": ("Fortaleza", "CE"),
    "curio": ("Fortaleza", "CE"),
    "jangurussu": ("Fortaleza", "CE"),

    # ── BA ──
    "alto do coqueirinho": ("Salvador", "BA"),

    # ── Bairros de São Paulo ──
    "morro dos ingleses": ("São Paulo", "SP"),
    "jardim paulista": ("São Paulo", "SP"),
    "cidade monções": ("São Paulo", "SP"),
    "cidade moncoes": ("São Paulo", "SP"),
    "jardim são paulo": ("São Paulo", "SP"),
    "jardim sao paulo": ("São Paulo", "SP"),
    "vila regente feijó": ("São Paulo", "SP"),
    "vila regente feijo": ("São Paulo", "SP"),
    "jardim vergueiro": ("São Paulo", "SP"),
    "jardim varginha": ("São Paulo", "SP"),
    "vila marieta": ("São Paulo", "SP"),

    # ── Outros bairros/localidades ──
    "jardim novo mundo": ("Goiânia", "GO"),
    "jardim das rosas": ("São Paulo", "SP"),
    "santana": ("São Paulo", "SP"),
    "vila da paz (novo glória)": ("Goiânia", "GO"),
    "vila da paz (novo gloria)": ("Goiânia", "GO"),
    "salinas": ("Salinas", "MG"),
    "itamarati": ("Manaus", "AM"),
    "parnaíba": ("Parnaíba", "PI"),
    "parnaiba": ("Parnaíba", "PI"),
    "são pedro": ("São Pedro", "SP"),
    "sao pedro": ("São Pedro", "SP"),
    "serrinha": ("Serrinha", "BA"),
    "rio das pedras": ("Rio das Pedras", "SP"),
    "barrinha": ("Barrinha", "SP"),
}


# ─── Helpers ─────────────────────────────────────────────

def _parse_data(s: str | None) -> datetime | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:19], fmt[:len(s[:19])]).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _parse_salario_texto(texto: str | None):
    if not texto:
        return None, None
    nums = re.findall(r"[\d]+(?:[.,]\d+)*", texto.replace(".", "").replace(",", ""))
    nums = [int(n) for n in nums if int(n) > 100]
    if not nums:
        return None, None
    return nums[0], nums[-1] if len(nums) > 1 else nums[0]


def _extrair_estado(location_str: str | None, area: list | None) -> tuple[str, str, str]:
    """
    Retorna (cidade, estado_sigla, regiao).

    Ordem de tentativas:
    1. area[] da Adzuna (campo estruturado)
    2. CIDADE_PARA_ESTADO — lookup direto por nome da cidade/bairro
    3. Parse da string de localização procurando sigla/nome de estado
    """
    cidade, estado, regiao = "", "", ""

    # ── 1. area[] da Adzuna ──────────────────────────────────────
    if area and len(area) >= 2:
        cidade = area[-1] if len(area) >= 3 else ""
        candidato = area[1].strip().lower()
        estado = ESTADOS_BR.get(candidato, "")

    # ── 2. Lookup por cidade/bairro ──────────────────────────────
    if not estado:
        # Tenta a cidade já extraída do area[]
        if cidade:
            lookup = CIDADE_PARA_ESTADO.get(cidade.lower().strip())
            if lookup:
                cidade, estado = lookup

        # Tenta cada parte da location_str
        if not estado and location_str:
            partes = [p.strip() for p in location_str.split(",")]
            for parte in partes:
                lookup = CIDADE_PARA_ESTADO.get(parte.lower().strip())
                if lookup:
                    cidade, estado = lookup
                    break
            # Se ainda não tem cidade, usa a primeira parte
            if not cidade and partes:
                cidade = partes[0].title()

    # ── 3. Fallback: parse da string procurando estado ───────────
    if not estado and location_str:
        partes = [p.strip().lower() for p in location_str.split(",")]
        for p in partes:
            if p in ESTADOS_BR:
                estado = ESTADOS_BR[p]
                break
        if not cidade and location_str:
            cidade = location_str.split(",")[0].strip().title()

    regiao = REGIOES.get(estado, "")
    return cidade, estado, regiao


def _extrair_skills(texto: str) -> tuple[list, list]:
    t = texto.lower()
    hard = [s for s in HARD_SKILLS if re.search(r'\b' + re.escape(s) + r'\b', t)]
    soft = [s for s in SOFT_SKILLS if re.search(r'\b' + re.escape(s) + r'\b', t)]
    return hard, soft


def _modalidade(contract_time: str | None, tipo_jooble: str | None) -> str:
    ct = (contract_time or "").lower()
    tj = (tipo_jooble or "").lower()
    if "remote" in ct or "remoto" in tj or "remote" in tj:
        return "Remoto"
    if "hybrid" in ct or "híbrido" in tj or "hybrid" in tj:
        return "Híbrido"
    return "Presencial"


def _jornada(contract_time: str | None, tipo_jooble: str | None) -> str:
    ct = (contract_time or "").lower()
    tj = (tipo_jooble or "").lower()
    if "part" in ct or "part" in tj or "meio" in tj:
        return "Meio Período"
    return "Integral"


def _nivel_experiencia(titulo: str, descricao: str) -> str:
    t = (titulo + " " + descricao).lower()
    if any(w in t for w in ["estágio", "estagio", "intern", "trainee"]):
        return "Estágio/Trainee"
    if any(w in t for w in ["júnior", "junior", "jr"]):
        return "Júnior"
    if any(w in t for w in ["pleno", "mid-level", "mid level"]):
        return "Pleno"
    if any(w in t for w in ["sênior", "senior", "sr.", "especialista"]):
        return "Sênior"
    if any(w in t for w in ["líder", "lider", "lead", "coordenador", "gerente", "manager", "diretor"]):
        return "Liderança"
    return "Não informado"


# ─── Normalizadores por fonte ────────────────────────────

def normalizar_adzuna(vaga: dict) -> dict:
    titulo     = vaga.get("title", "")
    descricao  = vaga.get("description", "")
    area       = vaga.get("location", {}).get("area", [])
    loc_str    = vaga.get("location", {}).get("display_name", "")
    cat_tag    = vaga.get("category", {}).get("tag", "")
    sal_min    = vaga.get("salary_min")
    sal_max    = vaga.get("salary_max")
    cidade, estado, regiao = _extrair_estado(loc_str, area)
    hard, soft = _extrair_skills(titulo + " " + descricao)

    return {
        "fonte_id":          f"adzuna_{vaga.get('id', '')}",
        "fonte":             "adzuna",
        "titulo":            titulo,
        "descricao":         descricao[:1000],
        "empresa":           vaga.get("company", {}).get("display_name", "Não informado"),
        "empresa_canonical": vaga.get("company", {}).get("canonical_name", ""),
        "cidade":            cidade,
        "estado":            estado,
        "regiao":            regiao,
        "latitude":          vaga.get("latitude"),
        "longitude":         vaga.get("longitude"),
        "salario_min":       float(sal_min) if sal_min else None,
        "salario_max":       float(sal_max) if sal_max else None,
        "salario_previsto":  vaga.get("salary_is_predicted") == "1",
        "categoria":         CATEGORIA_MAP.get(cat_tag, "Outros"),
        "categoria_original":vaga.get("category", {}).get("label", ""),
        "modalidade":        _modalidade(vaga.get("contract_time"), None),
        "jornada":           _jornada(vaga.get("contract_time"), None),
        "tipo_contrato":     vaga.get("contract_type", ""),
        "nivel_experiencia": _nivel_experiencia(titulo, descricao),
        "hard_skills":       hard,
        "soft_skills":       soft,
        "link":              vaga.get("redirect_url", ""),
        "data_publicacao":   _parse_data(vaga.get("created")),
    }


def normalizar_jooble(vaga: dict, categoria_busca: str = "Outros") -> dict:
    titulo    = vaga.get("title", "")
    descricao = vaga.get("snippet", "")
    loc_str   = vaga.get("location", "")
    sal_texto = vaga.get("salary", "")
    sal_min, sal_max = _parse_salario_texto(sal_texto)
    cidade, estado, regiao = _extrair_estado(loc_str, None)
    hard, soft = _extrair_skills(titulo + " " + descricao)

    return {
        "fonte_id":          f"jooble_{vaga.get('id', '')}",
        "fonte":             "jooble",
        "titulo":            titulo,
        "descricao":         descricao[:1000],
        "empresa":           vaga.get("company", "Não informado"),
        "empresa_canonical": (vaga.get("company") or "").lower().strip(),
        "cidade":            cidade,
        "estado":            estado,
        "regiao":            regiao,
        "latitude":          None,
        "longitude":         None,
        "salario_min":       float(sal_min) if sal_min else None,
        "salario_max":       float(sal_max) if sal_max else None,
        "salario_previsto":  False,
        "categoria":         categoria_busca,
        "categoria_original":vaga.get("type", ""),
        "modalidade":        _modalidade(None, vaga.get("type")),
        "jornada":           _jornada(None, vaga.get("type")),
        "tipo_contrato":     "",
        "nivel_experiencia": _nivel_experiencia(titulo, descricao),
        "hard_skills":       hard,
        "soft_skills":       soft,
        "link":              vaga.get("link", ""),
        "data_publicacao":   _parse_data(vaga.get("updated")),
    }


def remover_duplicatas(vagas: list[dict]) -> list[dict]:
    """Remove duplicatas pelo título + empresa normalizados."""
    vistas = set()
    resultado = []
    for v in vagas:
        chave = f"{v['titulo'].lower().strip()}_{v['empresa_canonical'].lower().strip()}"
        if chave not in vistas:
            vistas.add(chave)
            resultado.append(v)
    return resultado