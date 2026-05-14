"""
produtor_teste_produto.py
=========================
Simulador do microsserviço SDI.Micro.Produto (Equipe 2).

Publica eventos no tópico 'produto_cadastrado' do Redpanda local
usando o mesmo formato de envelope documentado no README da Equipe 2.

Como usar (com o venv ativado):
    python produtor_teste_produto.py

Pré-requisito: container Redpanda rodando via docker-compose-mensageria.yml
    docker compose -f docker-compose-mensageria.yml up -d
"""

import json
import uuid
from datetime import datetime, timezone

from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
BOOTSTRAP_SERVERS = "localhost:9092"
TOPICO = "produto_cadastrado"


# ---------------------------------------------------------------------------
# Garante que o tópico existe (cria se não existir)
# ---------------------------------------------------------------------------
def garantir_topico(topico: str) -> None:
    admin = AdminClient({"bootstrap.servers": BOOTSTRAP_SERVERS})
    metadata = admin.list_topics(timeout=5)
    if topico not in metadata.topics:
        novo_topico = NewTopic(topico, num_partitions=1, replication_factor=1)
        futuros = admin.create_topics([novo_topico])
        for t, fut in futuros.items():
            try:
                fut.result()
                print(f"✅ Tópico '{t}' criado com sucesso.")
            except Exception as e:
                print(f"⚠️  Tópico '{t}' já existe ou erro: {e}")
    else:
        print(f"ℹ️  Tópico '{topico}' já existe.")


# ---------------------------------------------------------------------------
# Monta o envelope no padrão exato da Equipe 2
# ---------------------------------------------------------------------------
def montar_envelope(event_type: str, payload: dict) -> str:
    envelope = {
        "eventId":       str(uuid.uuid4()),
        "eventType":     event_type,
        "eventVersion":  "1.0",
        "timestamp":     datetime.now(timezone.utc).isoformat(),
        "source":        "produtos-service",
        "correlationId": str(uuid.uuid4()),
        "payload":       payload,
    }
    return json.dumps(envelope, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Callback de entrega (confirma se chegou ao broker)
# ---------------------------------------------------------------------------
def delivery_report(err, msg):
    if err:
        print(f"  ❌ Falha na entrega: {err}")
    else:
        print(f"  ✅ Entregue → tópico={msg.topic()} | partição={msg.partition()} | offset={msg.offset()}")


# ---------------------------------------------------------------------------
# Eventos de simulação
# ---------------------------------------------------------------------------
# UUID fixo para poder testar atualização do mesmo produto
ID_PRODUTO_FIXO = "11111111-2222-3333-4444-555555555555"

EVENTOS = [
    # 1) Cadastro de um produto novo
    (
        "produto_cadastrado",
        {
            "id":               ID_PRODUTO_FIXO,
            "transporteId":     str(uuid.uuid4()),
            "categoriaId":      str(uuid.uuid4()),
            "unidadeMedidaId":  str(uuid.uuid4()),
            "codigo":           "NOTE-001",
            "nome":             "Notebook Dell Inspiron 15",
            "descricao":        "Notebook para uso acadêmico e profissional",
            "ativo":            True,
            "dataCadastro":     "2026-05-12T14:00:00Z",
            "ultimaAlteracao":  None,
        },
    ),
    # 2) Atualização do mesmo produto (nome mudou)
    (
        "produto_atualizado",
        {
            "id":               ID_PRODUTO_FIXO,
            "transporteId":     str(uuid.uuid4()),
            "categoriaId":      str(uuid.uuid4()),
            "unidadeMedidaId":  str(uuid.uuid4()),
            "codigo":           "NOTE-001",
            "nome":             "Notebook Dell Inspiron 15 (Atualizado)",
            "descricao":        "Versão atualizada do notebook",
            "ativo":            True,
            "dataCadastro":     "2026-05-12T14:00:00Z",
            "ultimaAlteracao":  "2026-05-12T15:00:00Z",
        },
    ),
    # 3) Inativação do mesmo produto
    (
        "produto_status_alterado",
        {
            "id":               ID_PRODUTO_FIXO,
            "transporteId":     str(uuid.uuid4()),
            "categoriaId":      str(uuid.uuid4()),
            "unidadeMedidaId":  str(uuid.uuid4()),
            "codigo":           "NOTE-001",
            "nome":             "Notebook Dell Inspiron 15 (Atualizado)",
            "descricao":        "Versão atualizada do notebook",
            "ativo":            False,   # <-- inativado
            "dataCadastro":     "2026-05-12T14:00:00Z",
            "ultimaAlteracao":  "2026-05-12T16:00:00Z",
        },
    ),
    # 4) Cadastro de um segundo produto (UUID aleatório a cada execução)
    (
        "produto_cadastrado",
        {
            "id":               str(uuid.uuid4()),
            "transporteId":     str(uuid.uuid4()),
            "categoriaId":      str(uuid.uuid4()),
            "unidadeMedidaId":  str(uuid.uuid4()),
            "codigo":           f"PROD-{str(uuid.uuid4())[:8].upper()}",
            "nome":             "Teclado Mecânico RGB",
            "descricao":        "Teclado gamer com switch blue",
            "ativo":            True,
            "dataCadastro":     "2026-05-12T14:30:00Z",
            "ultimaAlteracao":  None,
        },
    ),
    # 5) Evento de OUTRO domínio — deve ser ignorado pelo consumidor
    (
        "categoria_cadastrada",
        {
            "id":    str(uuid.uuid4()),
            "nome":  "Eletrônicos",
            "ativo": True,
        },
    ),
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("  🏭  Simulador SDI.Micro.Produto → Equipe 2")
    print(f"  Broker : {BOOTSTRAP_SERVERS}")
    print(f"  Tópico : {TOPICO}")
    print("=" * 60)

    garantir_topico(TOPICO)

    producer = Producer({"bootstrap.servers": BOOTSTRAP_SERVERS})

    print(f"\n📤 Publicando {len(EVENTOS)} evento(s)...\n")

    for i, (event_type, payload) in enumerate(EVENTOS, start=1):
        mensagem = montar_envelope(event_type, payload)
        print(f"[{i}/{len(EVENTOS)}] eventType='{event_type}'")
        producer.produce(
            topic=TOPICO,
            value=mensagem.encode("utf-8"),
            callback=delivery_report,
        )
        # Força entrega imediata (flush a cada mensagem para fins de teste)
        producer.flush()

    print("\n✅ Todos os eventos foram publicados!")
    print("\n💡 Verifique nos logs do FastAPI (outro terminal) se o consumidor processou os eventos.")
    print(f"   Espera-se 4 linhas de processamento e 1 evento ignorado (categoria_cadastrada).")
    print(f"\n🌐 Você também pode inspecionar as mensagens no Redpanda Console:")
    print(f"   http://localhost:8080  →  Topics → {TOPICO}")


if __name__ == "__main__":
    main()
