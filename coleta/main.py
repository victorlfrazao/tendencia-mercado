"""
main.py
Ponto de entrada: executa coleta → normalização → carga no banco.

Uso:
    python main.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from coletor import coletar_tudo
from carregador import carregar

if __name__ == "__main__":
    print("=" * 50)
    print("  Tendências de Mercado — Coleta de Dados")
    print("=" * 50)

    print("\n📡 Iniciando coleta das APIs...")
    vagas = coletar_tudo()

    print("\n🗄️  Carregando no banco de dados...")
    carregar(vagas)

    print("\n🎉 Pipeline concluído com sucesso!")
