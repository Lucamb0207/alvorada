"""
Parse daily WhatsApp production report and save to PostgreSQL.

Usage:
    python parse_report.py

Then paste the WhatsApp message and press Ctrl+Z (Windows) or Ctrl+D (Mac/Linux) + Enter.

Requires DATABASE_URL environment variable pointing to the Render PostgreSQL.
Set it before running:
    Windows:  $env:DATABASE_URL = "postgresql://..."
    Mac/Linux: export DATABASE_URL="postgresql://..."
"""

import re
import sys
from datetime import datetime
import db

# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _clean(text: str) -> str:
    for ch in ["‎", "‏", "‪", "‬", "​", "⁠"]:
        text = text.replace(ch, "")
    return text


def _int(text: str, pattern: str, flags=0):
    m = re.search(pattern, text, flags)
    return int(m.group(1).replace(".", "").replace(",", "")) if m else None


def parse_text(raw: str) -> dict:
    text = _clean(raw)

    data = {"raw_text": raw}

    # Date
    m = re.search(r"[Ff]echa[:\s*]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})", text)
    if not m:
        raise ValueError("Data (Fecha) não encontrada no report.")
    date_str = m.group(1).replace("/", "-")
    data["fecha"] = datetime.strptime(date_str, "%d-%m-%Y").date()

    # PB bruto
    data["pb_bls"] = _int(text, r"PB[:\s]+(\d[\d\.,]*)\s*[Bb]ls")

    # PN neto (dia)
    data["pn_bls"] = _int(text, r"PN[:\s]+(\d[\d\.,]*)\s*[Bb]ls")

    # OFERTA
    data["oferta_bls"] = _int(text, r"OFERTA[:\s]+(\d[\d\.,]*)\s*[Bb]ls")

    # Prom MES Operada
    m = re.search(r"MES\s+Operada[^B]*BN[:\s]+(\d+)", text, re.DOTALL | re.IGNORECASE)
    data["prom_mes_operada"] = int(m.group(1)) if m else None

    # Prom MES Fiscalizada
    m = re.search(r"MES\s+Fiscalizada[^B]*BN[:\s]+(\d+)", text, re.DOTALL | re.IGNORECASE)
    data["prom_mes_fiscalizada"] = int(m.group(1)) if m else None

    # PDT Plan
    m = re.search(r"PDT\)[^\d]*BN[:\s]+(\d+)", text, re.IGNORECASE)
    data["pdt_plan"] = int(m.group(1)) if m else None

    # VAR vs PDT (e.g. "VAR: - 88 BLS" or "VAR: + 12 BLS")
    m = re.search(r"VAR[:\s]+([-+–\s]+)(\d+)\s*BLS", text, re.IGNORECASE)
    if m:
        sign = -1 if "-" in m.group(1) or "–" in m.group(1) else 1
        data["var_vs_pdt"] = sign * int(m.group(2))
    else:
        data["var_vs_pdt"] = None

    # Variação diária (e.g. "Var: + 653bls")
    m = re.search(r"[Vv]ar[:\s]+([-+–\s]+)(\d+)\s*bls", text)
    if m:
        sign = -1 if "-" in m.group(1) or "–" in m.group(1) else 1
        data["var_diaria"] = sign * int(m.group(2))
    else:
        data["var_diaria"] = None

    # Falhas — bullet points after "Explicaciones"
    m = re.search(r"[Ee]xplicaciones[:\s]+(.*?)(?=📊|Plan\s+\w+\s+\d{4}|\Z)", text, re.DOTALL)
    if m:
        block = m.group(1)
        bullets = re.findall(r"[*•]\s*(.+?)(?=\n\s*[*•]|\Z)", block, re.DOTALL)
        falhas_lines = [b.strip().replace("\n", " ") for b in bullets if b.strip()]
        data["falhas"] = "\n".join(falhas_lines)
    else:
        data["falhas"] = ""

    return data


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 55)
    print("  Parser de Report de Produção — Consórcio Alvorada")
    print("=" * 55)
    print("\nCole o texto do WhatsApp abaixo.")
    print("Quando terminar: pressione Enter, depois Ctrl+Z (Windows) ou Ctrl+D (Mac/Linux), depois Enter.\n")

    lines = []
    try:
        while True:
            lines.append(input())
    except EOFError:
        pass

    text = "\n".join(lines)
    if not text.strip():
        print("❌ Nenhum texto recebido.")
        sys.exit(1)

    try:
        data = parse_text(text)
    except ValueError as e:
        print(f"❌ Erro ao parsear: {e}")
        sys.exit(1)

    print("\n📊 Dados extraídos:")
    print(f"   Data      : {data['fecha']}")
    print(f"   PB bruto  : {data.get('pb_bls')} bls")
    print(f"   PN neto   : {data.get('pn_bls')} bls")
    print(f"   OFERTA    : {data.get('oferta_bls')} bls")
    print(f"   Prom Mês  : {data.get('prom_mes_operada')} bls (Operada)")
    print(f"   PDT Plan  : {data.get('pdt_plan')} bls")
    var = data.get("var_vs_pdt")
    sinal = "+" if var and var > 0 else ""
    print(f"   VAR/PDT   : {sinal}{var} bls")
    print(f"   VAR diária: {data.get('var_diaria')} bls")
    if data.get("falhas"):
        print(f"   Falhas    : {len(data['falhas'].splitlines())} itens")

    confirm = input("\nSalvar no banco? (s/n): ").strip().lower()
    if confirm == "s":
        db.upsert_producao(data)
        print(f"✅ Report de {data['fecha']} salvo com sucesso!")
    else:
        print("Cancelado.")
