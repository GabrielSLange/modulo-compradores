import json
import uuid
from datetime import datetime, timezone
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic

BOOTSTRAP_SERVERS = "localhost:9092"

TOPICOS = [
    "produto_cadastrado",
    "produto_atualizado",
    "produto_status_alterado"
]

def garantir_topicos() -> None:
    admin = AdminClient({"bootstrap.servers": BOOTSTRAP_SERVERS})
    metadata = admin.list_topics(timeout=5)
    
    novos_topicos = []
    for topico in TOPICOS:
        if topico not in metadata.topics:
            novos_topicos.append(NewTopic(topico, num_partitions=1, replication_factor=1))
            
    if novos_topicos:
        futuros = admin.create_topics(novos_topicos)
        for t, fut in futuros.items():
            try:
                fut.result()
                print(f"Topico '{t}' criado com sucesso.")
            except Exception as e:
                print(f"Erro ao criar topico '{t}': {e}")
    else:
        print("Todos os topicos ja existem no Redpanda.")

def delivery_report(err, msg):
    if err is not None:
        print(f"Falha ao entregar mensagem: {err}")
    else:
        print(f"Mensagem entregue em {msg.topic()} [{msg.partition()}] offset {msg.offset()}")

def _get_iso_now():
    return datetime.now(timezone.utc).isoformat()

def montar_envelope(event_type: str, payload: dict) -> str:
    envelope = {
        "eventId": str(uuid.uuid4()),
        "eventType": event_type,
        "eventVersion": "1.0",
        "timestamp": _get_iso_now(),
        "source": "produtos-service",
        "correlationId": str(uuid.uuid4()),
        "payload": payload,
    }
    return json.dumps(envelope)

id_produto_teste = str(uuid.uuid4())

EVENTOS = [
    (
        "produto_cadastrado",
        {
            "id": id_produto_teste,
            "transporteId": str(uuid.uuid4()),
            "categoriaId": str(uuid.uuid4()),
            "unidadeMedidaId": str(uuid.uuid4()),
            "codigo": "1234",
            "nome": "Produto Teste 124",
            "descricao": "Descricao do produto 4324",
            "ativo": True,
            "dataCadastro": _get_iso_now(),
            "ultimaAlteracao": None
        }
    ),
    (
        "produto_atualizado",
        {
            "id": id_produto_teste,
            "transporteId": str(uuid.uuid4()),
            "categoriaId": str(uuid.uuid4()),
            "unidadeMedidaId": str(uuid.uuid4()),
            "codigo": "1234",
            "nome": "Produto Teste 124 Atualizado",
            "descricao": "Descricao do produto 4324 alterada",
            "ativo": True,
            "dataCadastro": _get_iso_now(),
            "ultimaAlteracao": _get_iso_now()
        }
    ),
    (
        "produto_status_alterado",
        {
            "id": id_produto_teste,
            "transporteId": str(uuid.uuid4()),
            "categoriaId": str(uuid.uuid4()),
            "unidadeMedidaId": str(uuid.uuid4()),
            "codigo": "1234",
            "nome": "Produto Teste 124 Atualizado",
            "descricao": "Descricao do produto 4324 alterada",
            "ativo": False,
            "dataCadastro": _get_iso_now(),
            "ultimaAlteracao": _get_iso_now()
        }
    )
]

def main():
    print("Iniciando simulador SDI.Micro.Produto (Equipe 2)")
    
    garantir_topicos()
    producer = Producer({"bootstrap.servers": BOOTSTRAP_SERVERS})

    print(f"Publicando {len(EVENTOS)} evento(s)...")

    for i, (event_type, payload) in enumerate(EVENTOS, start=1):
        mensagem = montar_envelope(event_type, payload)
        
        print(f"[{i}/{len(EVENTOS)}] Publicando no topico '{event_type}'")
        producer.produce(
            topic=event_type,
            value=mensagem.encode("utf-8"),
            callback=delivery_report,
        )
        producer.flush()

if __name__ == "__main__":
    main()