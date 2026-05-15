from confluent_kafka import Consumer, KafkaError
import os

def iniciar_consumidor():
    servidor_kafka = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "10.128.0.2:9092,10.128.0.3:9092,10.128.0.4:9092")
    topico = "demanda_criada"

    # Configuração de quem está lendo
    conf = {
        'bootstrap.servers': servidor_kafka,
        'group.id': 'grupo-teste-local',
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(conf)
    consumer.subscribe([topico])

    print(f"🎧 Escutando o tópico '{topico}'... (Aperte Ctrl+C para parar)")

    try:
        while True:
            # Fica esperando mensagens por 1 segundo, se não chegar, repete o loop
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(msg.error())
                    break

            # Mensagem chegou! Decodifica e imprime na tela
            print(f"\n[CONSUMER] 📬 Nova mensagem recebida!")
            print(f"Chave: {msg.key().decode('utf-8')}")
            print(f"Valor: {msg.value().decode('utf-8')}")
            print("-" * 30)

    except KeyboardInterrupt:
        print("\nParando o consumidor de testes...")
    finally:
        consumer.close()

if __name__ == "__main__":
    iniciar_consumidor()