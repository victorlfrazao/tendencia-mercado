"""
carregador.py
Cria as tabelas no PostgreSQL e salva as vagas normalizadas.
"""
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")


def conectar():
    return psycopg2.connect(DB_URL)


def criar_tabelas(conn):
    """Cria as tabelas se não existirem."""
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS vagas (
            id                  SERIAL PRIMARY KEY,
            fonte_id            VARCHAR(100) UNIQUE NOT NULL,
            fonte               VARCHAR(20) NOT NULL,
            titulo              TEXT,
            descricao           TEXT,
            empresa             TEXT,
            empresa_canonical   TEXT,
            cidade              TEXT,
            estado              VARCHAR(2),
            regiao              VARCHAR(20),
            latitude            FLOAT,
            longitude           FLOAT,
            salario_min         FLOAT,
            salario_max         FLOAT,
            salario_previsto    BOOLEAN DEFAULT FALSE,
            categoria           VARCHAR(50),
            categoria_original  TEXT,
            modalidade          VARCHAR(20),
            jornada             VARCHAR(20),
            tipo_contrato       VARCHAR(30),
            nivel_experiencia   VARCHAR(30),
            hard_skills         TEXT[],
            soft_skills         TEXT[],
            link                TEXT,
            data_publicacao     TIMESTAMPTZ,
            coletado_em         TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_vagas_categoria  ON vagas(categoria);
        CREATE INDEX IF NOT EXISTS idx_vagas_estado     ON vagas(estado);
        CREATE INDEX IF NOT EXISTS idx_vagas_empresa    ON vagas(empresa_canonical);
        CREATE INDEX IF NOT EXISTS idx_vagas_data       ON vagas(data_publicacao);
        CREATE INDEX IF NOT EXISTS idx_vagas_fonte      ON vagas(fonte);
        """)
        conn.commit()
    print("✅ Tabelas criadas/verificadas")


def filtrar_recentes(vagas: list[dict]) -> list[dict]:
    """Remove vagas com mais de 1 ano."""
    limite = datetime.now(timezone.utc) - timedelta(days=365)
    recentes = []
    for v in vagas:
        dp = v.get("data_publicacao")
        if dp is None or dp >= limite:
            recentes.append(v)
    print(f"📅 Filtro de 1 ano: {len(vagas)} → {len(recentes)} vagas")
    return recentes


def salvar_vagas(conn, vagas: list[dict]) -> tuple[int, int]:
    """Insere vagas no banco. Retorna (inseridas, ignoradas)."""
    inseridas = 0
    ignoradas = 0

    with conn.cursor() as cur:
        for v in vagas:
            try:
                cur.execute("""
                    INSERT INTO vagas (
                        fonte_id, fonte, titulo, descricao, empresa, empresa_canonical,
                        cidade, estado, regiao, latitude, longitude,
                        salario_min, salario_max, salario_previsto,
                        categoria, categoria_original, modalidade, jornada,
                        tipo_contrato, nivel_experiencia,
                        hard_skills, soft_skills, link, data_publicacao
                    ) VALUES (
                        %(fonte_id)s, %(fonte)s, %(titulo)s, %(descricao)s,
                        %(empresa)s, %(empresa_canonical)s,
                        %(cidade)s, %(estado)s, %(regiao)s,
                        %(latitude)s, %(longitude)s,
                        %(salario_min)s, %(salario_max)s, %(salario_previsto)s,
                        %(categoria)s, %(categoria_original)s,
                        %(modalidade)s, %(jornada)s, %(tipo_contrato)s,
                        %(nivel_experiencia)s,
                        %(hard_skills)s, %(soft_skills)s,
                        %(link)s, %(data_publicacao)s
                    )
                    ON CONFLICT (fonte_id) DO UPDATE SET
                        titulo            = EXCLUDED.titulo,
                        salario_min       = EXCLUDED.salario_min,
                        salario_max       = EXCLUDED.salario_max,
                        hard_skills       = EXCLUDED.hard_skills,
                        soft_skills       = EXCLUDED.soft_skills,
                        coletado_em       = NOW();
                """, v)
                inseridas += 1
            except Exception as e:
                ignoradas += 1
                print(f"  ⚠️  Erro ao salvar {v.get('fonte_id')}: {e}")

        conn.commit()
    return inseridas, ignoradas


def carregar(vagas: list[dict]):
    """Pipeline completo: conecta → cria tabelas → filtra → salva."""
    print("\n🗄️  Conectando ao PostgreSQL...")
    conn = conectar()
    criar_tabelas(conn)

    vagas_recentes = filtrar_recentes(vagas)
    print(f"\n💾 Salvando {len(vagas_recentes)} vagas no banco...")
    inseridas, ignoradas = salvar_vagas(conn, vagas_recentes)

    print(f"\n✅ Concluído: {inseridas} inseridas/atualizadas, {ignoradas} com erro")
    conn.close()


if __name__ == "__main__":
    # Teste rápido de conexão
    try:
        conn = conectar()
        criar_tabelas(conn)
        conn.close()
        print("✅ Conexão com o banco OK!")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
