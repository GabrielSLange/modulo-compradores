import uuid
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from Data.database import SessionLocal
from Models.demanda_model import Demanda
from Models.demanda_recorrencia_model import DemandaRecorrencia
from Events.Producers.demanda_producer import DemandaProducer

def processar_recorrencias():
    print("\n[JOB] 🔄 Iniciando varredura de demandas recorrentes (Produção)...")
    db: Session = SessionLocal()
    
    try:
        hoje = datetime.now().date()
        
        recorrencias_ativas = db.query(DemandaRecorrencia).filter(
            (DemandaRecorrencia.data_fim >= hoje) | (DemandaRecorrencia.data_fim == None)
        ).all()

        if not recorrencias_ativas:
            print("[JOB] 💤 Nenhuma recorrência ativa para processar hoje.")
            return

        demandas_geradas = 0

        for rec in recorrencias_ativas:
            # 1. VALIDAÇÃO DE FREQUÊNCIA (A "inteligência" de produção)
            gerar_hoje = False
            
            # Se a data de início for no futuro, ignora
            if rec.data_inicio > hoje:
                continue

            # Normaliza (lower + tolera acento): o DTO documenta "diaria" sem acento,
            # mas a comparacao antiga exigia "diária" com acento e nunca batia.
            freq = (rec.frequencia or "").strip().lower()
            if freq in ("diaria", "diária"):
                gerar_hoje = True
            elif freq == "semanal":
                # Verifica se o dia da semana de hoje é o mesmo dia da semana em que começou
                if hoje.weekday() == rec.data_inicio.weekday():
                    gerar_hoje = True
            elif freq == "mensal":
                # Verifica se o dia do mês é igual ao dia de início
                if hoje.day == rec.data_inicio.day:
                    gerar_hoje = True
            
            if not gerar_hoje:
                continue # Pula para a próxima recorrência da lista

            # 2. GERAÇÃO DA DEMANDA
            demanda_pai = db.query(Demanda).filter(Demanda.id_demanda == rec.id_demanda).first()
            if not demanda_pai:
                continue

            nova_demanda = Demanda(
                id_empresa_comprador=demanda_pai.id_empresa_comprador,
                id_usuario_criador=demanda_pai.id_usuario_criador,
                id_produto=demanda_pai.id_produto,
                id_endereco_destino=demanda_pai.id_endereco_destino,
                quantidade_desejada=rec.quantidade_por_periodo,
                preco_maximo=demanda_pai.preco_maximo,
                prioridade=demanda_pai.prioridade,
                is_recorrente=False, # A instância gerada é um pedido único
                status="aberta"
            )
            
            db.add(nova_demanda)
            db.flush() 

            payload_evento = {
                "id_empresa_comprador": nova_demanda.id_empresa_comprador,
                "id_produto": nova_demanda.id_produto,
                "quantidade_desejada": float(nova_demanda.quantidade_desejada),
                "demanda_pai_origem": demanda_pai.id_demanda 
            }
            
            DemandaProducer.publicar_demanda_recorrente_gerada(nova_demanda.id_demanda, payload_evento)
            demandas_geradas += 1

        db.commit()
        print(f"[JOB] ✅ Varredura concluída. {demandas_geradas} demandas geradas hoje.")

    except Exception as e:
        db.rollback()
        print(f"[JOB ERRO] Falha ao processar as recorrências: {str(e)}")
    finally:
        db.close()

def iniciar_scheduler():
    scheduler = BackgroundScheduler()
    # CONFIGURAÇÃO DE PRODUÇÃO: Executa todos os dias exatamente à meia-noite (00:00)
    scheduler.add_job(processar_recorrencias, 'cron', hour=0, minute=0)
    scheduler.start()