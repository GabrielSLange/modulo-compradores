"""
Teste manual de idempotência do pedido_consumer.

Executa contra o SQLite local (banco_local_teste.db). Use após rodar
seed.py — depende de uma demanda com status='aberta' e is_pedido=False.

Rode dentro de backend/:
    python teste_pedido_consumer_idempotencia.py
"""
import sys

from Data.database import SessionLocal
# Importar todos os Models antes de usar Demanda — necessário para
# o SQLAlchemy resolver relationship("EnderecoEntrega") por nome.
from Models import (  # noqa: F401
    endereco_entrega_model,
    demanda_model,
    demanda_recorrencia_model,
    wishlist_item_model,
    produto_cache_model,
)
from Models.demanda_model import Demanda
from Events.Consumers.pedido_consumer import processar_evento_pedido


def _encontrar_demanda_aberta_id() -> str:
    with SessionLocal() as db:
        demanda = db.query(Demanda).filter(
            Demanda.status == "aberta",
            Demanda.is_pedido == False
        ).first()
        if not demanda:
            print(
                "ERRO: nenhuma demanda 'aberta' (is_pedido=False) encontrada. "
                "Rode seed.py primeiro.",
                file=sys.stderr,
            )
            sys.exit(1)
        return demanda.id_demanda


def _estado(id_demanda: str) -> tuple[bool, str]:
    with SessionLocal() as db:
        d = db.query(Demanda).filter(Demanda.id_demanda == id_demanda).first()
        return bool(d.is_pedido), str(d.status)


def main() -> int:
    id_demanda = _encontrar_demanda_aberta_id()
    print(f"Usando demanda: {id_demanda}")

    evento = {
        "eventId": "evt-teste-idempotencia-1",
        "eventType": "pedido_criado",
        "correlationId": "corr-teste",
        "payload": {
            "id_demanda": id_demanda,
            "id_pedido": "pedido-fake-1",
            "status": "processando",
        },
    }

    is_pedido_antes, status_antes = _estado(id_demanda)
    print(f"Antes:           is_pedido={is_pedido_antes}, status={status_antes!r}")
    assert is_pedido_antes is False and status_antes == "aberta", "Estado inicial inesperado"

    print("\n-> 1a chamada (deve promover):")
    processar_evento_pedido(evento)
    is_pedido_meio, status_meio = _estado(id_demanda)
    print(f"  Depois:        is_pedido={is_pedido_meio}, status={status_meio!r}")
    assert is_pedido_meio is True and status_meio == "atendida", "1a chamada nao promoveu"

    print("\n-> 2a chamada (deve ser idempotente, logar 'duplicado ignorado'):")
    processar_evento_pedido(evento)
    is_pedido_fim, status_fim = _estado(id_demanda)
    print(f"  Depois:        is_pedido={is_pedido_fim}, status={status_fim!r}")
    assert is_pedido_fim is True and status_fim == "atendida", "2a chamada alterou estado"

    print("\nOK Idempotencia confirmada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
