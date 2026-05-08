import json
import os
from confluent_kafka import Producer

class DemandaProducer:
    @staticmethod
    def _obter_produtor():
        # Busca o endereço do Kafka no .env, se não achar, usa o Redpanda local na porta 9092
        servidor_kafka = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        conf = {
            'bootstrap.servers': servidor_kafka,
            'client.id': 'modulo-compradores-producer'
        }
        return Producer(conf)

    @staticmethod
    def publicar_demanda_criada(id_demanda: str, dados_demanda: dict):
        try:
            producer = DemandaProducer._obter_produtor()
            topico = "evento_demanda_criada" # O nome da nossa caixa de correio
            
            # Converte os dados para texto (JSON), pois o servidor só entende texto/bytes
            mensagem = json.dumps({
                "id_demanda": id_demanda,
                "dados": dados_demanda
            })

            # Dispara a mensagem
            producer.produce(topic=topico, key=id_demanda, value=mensagem)
            
            # Força o envio imediato
            producer.flush()
            print(f"[PRODUCER] 🚀 Evento disparado com sucesso! Demanda ID: {id_demanda}")
            
        except Exception as e:
            print(f"[ERRO MENSAGERIA] Falha ao enviar evento: {str(e)}")