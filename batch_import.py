"""
Importação em lote de relatórios de produção.

Usage:
    python batch_import.py

Cole todos os relatórios do WhatsApp separados por uma linha contendo apenas ===
Quando terminar: pressione Enter, depois Ctrl+Z (Windows) ou Ctrl+D (Mac/Linux), depois Enter.

Requires DATABASE_URL environment variable (External URL do Render).
"""

import sys
from parse_report import parse_text
import db


SEPARATOR = "==="


def main():
    print("=" * 60)
    print("  Importação em Lote — Consórcio Alvorada")
    print("=" * 60)
    print(f"\nCole os relatórios separados por uma linha com '{SEPARATOR}'.")
    print("Quando terminar: Enter → Ctrl+Z (Windows) / Ctrl+D (Mac) → Enter.\n")

    lines = []
    try:
        while True:
            lines.append(input())
    except EOFError:
        pass

    raw = "\n".join(lines).strip()
    if not raw:
        print("Nenhum texto recebido.")
        sys.exit(1)

    blocks = [b.strip() for b in raw.split(SEPARATOR) if b.strip()]
    print(f"\n{len(blocks)} relatório(s) encontrado(s).\n")

    parsed_list = []
    for i, block in enumerate(blocks, 1):
        try:
            data = parse_text(block)
            parsed_list.append(data)
            var = data.get("var_vs_pdt")
            sinal = "+" if var and var > 0 else ""
            print(
                f"  [{i}] {data['fecha']}  "
                f"PB={data.get('pb_bls')}  "
                f"PN={data.get('pn_bls')}  "
                f"PDT={data.get('pdt_plan')}  "
                f"VAR={sinal}{var}"
            )
        except ValueError as e:
            print(f"  [{i}] ERRO ao parsear bloco {i}: {e}")

    if not parsed_list:
        print("\nNenhum relatório válido. Verifique os textos.")
        sys.exit(1)

    print(f"\n{len(parsed_list)} relatório(s) prontos para salvar.")
    confirm = input("Salvar todos no banco? (s/n): ").strip().lower()
    if confirm != "s":
        print("Cancelado.")
        sys.exit(0)

    ok = 0
    for data in parsed_list:
        try:
            db.upsert_producao(data)
            print(f"  ✓ {data['fecha']} salvo.")
            ok += 1
        except Exception as e:
            print(f"  ✗ {data['fecha']} erro: {e}")

    print(f"\n{ok}/{len(parsed_list)} relatório(s) salvos com sucesso.")


if __name__ == "__main__":
    main()
