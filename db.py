import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_conn():
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL não definida.")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(url)


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS producao (
                    id          SERIAL PRIMARY KEY,
                    fecha       DATE UNIQUE NOT NULL,
                    pb_bls      INTEGER,
                    pn_bls      INTEGER,
                    oferta_bls  INTEGER,
                    prom_mes_operada     INTEGER,
                    prom_mes_fiscalizada INTEGER,
                    pdt_plan    INTEGER,
                    var_vs_pdt  INTEGER,
                    var_diaria  INTEGER,
                    falhas      TEXT,
                    raw_text    TEXT,
                    created_at  TIMESTAMP DEFAULT NOW()
                )
            """)
        conn.commit()


def upsert_producao(data: dict):
    init_db()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO producao
                    (fecha, pb_bls, pn_bls, oferta_bls, prom_mes_operada,
                     prom_mes_fiscalizada, pdt_plan, var_vs_pdt, var_diaria, falhas, raw_text)
                VALUES
                    (%(fecha)s, %(pb_bls)s, %(pn_bls)s, %(oferta_bls)s, %(prom_mes_operada)s,
                     %(prom_mes_fiscalizada)s, %(pdt_plan)s, %(var_vs_pdt)s, %(var_diaria)s,
                     %(falhas)s, %(raw_text)s)
                ON CONFLICT (fecha) DO UPDATE SET
                    pb_bls               = EXCLUDED.pb_bls,
                    pn_bls               = EXCLUDED.pn_bls,
                    oferta_bls           = EXCLUDED.oferta_bls,
                    prom_mes_operada     = EXCLUDED.prom_mes_operada,
                    prom_mes_fiscalizada = EXCLUDED.prom_mes_fiscalizada,
                    pdt_plan             = EXCLUDED.pdt_plan,
                    var_vs_pdt           = EXCLUDED.var_vs_pdt,
                    var_diaria           = EXCLUDED.var_diaria,
                    falhas               = EXCLUDED.falhas,
                    raw_text             = EXCLUDED.raw_text
            """, data)
        conn.commit()


def fetch_producao(days: int = 60):
    try:
        init_db()
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT fecha, pn_bls, pb_bls, oferta_bls, pdt_plan,
                           prom_mes_operada, prom_mes_fiscalizada,
                           var_vs_pdt, var_diaria, falhas
                    FROM producao
                    ORDER BY fecha ASC
                    LIMIT %s
                """, (days,))
                return [dict(r) for r in cur.fetchall()]
    except Exception as exc:
        print(f"[db] fetch_producao error: {exc}")
        return []
