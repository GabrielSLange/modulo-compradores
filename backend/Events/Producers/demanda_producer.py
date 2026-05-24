import json
import os
import uuid
from datetime import datetime, timezone
from confluent_kafka import Producer

class DemandaProducer:
    @staticmethod
    def _obter_produtor():
        servidor_kafka = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "10.128.0.2:9092,10.128.0.3:9092,10.128.0.4:9092")
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

    @staticmethod
    def publicar_demanda_recorrente_gerada(id_nova_demanda: str, dados_demanda: dict):
        try:
            producer = DemandaProducer._obter_produtor()
            topico = "demanda_recorrente_gerada" 
            
            evento = {
                "eventId": str(uuid.uuid4()),
                "eventType": "demanda_recorrente_gerada",
                "eventVersion": "1.0",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "source": "modulo-compradores",
                "correlationId": id_nova_demanda, 
                "payload": dados_demanda
            }

            mensagem = json.dumps(evento)
            producer.produce(topic=topico, key=id_nova_demanda, value=mensagem)
            producer.flush()
            
            print(f"[JOB KAFKA] 🤖 Demanda recorrente gerada automaticamente! ID: {id_nova_demanda}")

        except Exception as e:
            print(f"[ERRO MENSAGERIA] Falha ao enviar evento de recorrência: {str(e)}")

    @staticmethod
    def publicar_pedido_criado(id_demanda: str, dados_pedido: dict):
        """Publica evento quando demanda eh promovida pra pedido (Solucao 1).

        Source = modulo-compradores, pra que nosso proprio pedido_consumer
        possa ignorar (anti-loop). Equipes externas (negociacao) consomem normal.
        """
        try:
            producer = DemandaProducer._obter_produtor()
            topico = "pedido_criado"

            evento = {
                "eventId": str(uuid.uuid4()),
                "eventType": "pedido_criado",
                "eventVersion": "1.0",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "source": "modulo-compradores",
                "correlationId": id_demanda,
                "payload": dados_pedido
            }

            producer.produce(topic=topico, key=id_demanda, value=json.dumps(evento))
            producer.flush()
            print(f"[PRODUCER] 🚀 pedido_criado disparado. Demanda promovida: {id_demanda}")
        except Exception as e:
            print(f"[ERRO MENSAGERIA] Falha ao publicar pedido_criado: {str(e)}")

    @staticmethod
    def publicar_pedido_atualizado(id_demanda: str, dados_pedido: dict):
        """Publica evento quando um pedido (demanda com is_pedido=true) muda de status.

        Hoje so disparado quando um pedido eh cancelado. Outros status no futuro.
        """
        try:
            producer = DemandaProducer._obter_produtor()
            topico = "pedido_atualizado"

            evento = {
                "eventId": str(uuid.uuid4()),
                "eventType": "pedido_atualizado",
                "eventVersion": "1.0",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "source": "modulo-compradores",
                "correlationId": id_demanda,
                "payload": dados_pedido
            }

            producer.produce(topic=topico, key=id_demanda, value=json.dumps(evento))
            producer.flush()
            print(f"[PRODUCER] 🚀 pedido_atualizado disparado. Pedido: {id_demanda}")
        except Exception as e:
            print(f"[ERRO MENSAGERIA] Falha ao publicar pedido_atualizado: {str(e)}")