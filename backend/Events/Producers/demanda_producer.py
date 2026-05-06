class DemandaProducer:
    @staticmethod
    def publicar_demanda_criada(id_demanda: str, dados_demanda: dict):
        """
        No futuro, este método usará a biblioteca 'confluent-kafka' para
        disparar o evento no formato JSON exigido pela equipe de infra.
        """
        # TODO: Implementar conexão real com Kafka (KAFKA_BOOTSTRAP_SERVERS)
        print(f"[KAFKA MOCK] 🚀 Evento 'demanda_criada' publicado no tópico! Demanda ID: {id_demanda}")