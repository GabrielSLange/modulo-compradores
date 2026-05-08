import json
import os
import uuid
from datetime import datetime, timezone
from confluent_kafka import Producer

class DemandaProducer:
    @staticmethod
    def _obter_produtor():
        servidor_kafka = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        conf = {
            'bootstrap.servers': servidor_kafka,
            'client.id': 'modulo-compradores'
        }
        return Producer(conf)

    @staticmethod
    def publicar_demanda_criada(id_demanda: str, dados_demanda: dict):
        try:
            producer = DemandaProducer._obter_produtor()
            
            # 1. Ajuste do nome do Tópico conforme PDF do professor
            topico = "demanda_criada" 
            
            # 2. Construindo o Envelope do Evento no padrão exato exigido
            evento = {
                "eventId": str(uuid.uuid4()),
                "eventType": "demanda_criada",
                "eventVersion": "1.0",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), # Formato ISO8601
                "source": "modulo-compradores",
                "correlationId": id_demanda, # Usando o ID da demanda como correlação para facilitar rastreio
                "payload": dados_demanda
            }

            mensagem = json.dumps(evento)

            # Envia a mensagem usando o ID da demanda como Key (exigência do professor)
            producer.produce(topic=topico, key=id_demanda, value=mensagem)
            producer.flush()
            
            print(f"[PRODUCER] 🚀 Evento padronizado disparado! Demanda ID: {id_demanda}")
            
        except Exception as e:
            print(f"[ERRO MENSAGERIA] Falha ao enviar evento: {str(e)}")