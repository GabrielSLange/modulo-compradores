from sqlalchemy.orm import Session
from Models.demanda_model import Demanda
from Models.demanda_recorrencia_model import DemandaRecorrencia
from DTOs.Request.demanda_create_dto import DemandaCreateDTO
from Events.Producers.demanda_producer import DemandaProducer
from sqlalchemy import desc

class DemandaService:
    @staticmethod
    def criar_demanda(db: Session, dto: DemandaCreateDTO):
        # 1. Cria a Demanda (A Raiz)
        nova_demanda = Demanda(
            id_empresa_comprador=dto.id_empresa_comprador,
            id_usuario_criador=dto.id_usuario_criador,
            id_produto=dto.id_produto,
            id_endereco_destino=dto.id_endereco_destino,
            quantidade_desejada=dto.quantidade_desejada,
            preco_maximo=dto.preco_maximo,
            prioridade=dto.prioridade,
            is_recorrente=dto.is_recorrente,
            status="aberta"
        )
        db.add(nova_demanda)
        db.flush() # Salva temporariamente para gerar o ID da demanda

        # 2. Cria a Recorrência (O Filho) na mesma transação, se existir
        if dto.is_recorrente and dto.recorrencia:
            nova_recorrencia = DemandaRecorrencia(
                id_demanda=nova_demanda.id_demanda,
                frequencia=dto.recorrencia.frequencia,
                quantidade_por_periodo=dto.recorrencia.quantidade_por_periodo,
                data_inicio=dto.recorrencia.data_inicio,
                data_fim=dto.recorrencia.data_fim,
                dia_preferencial=dto.recorrencia.dia_preferencial
            )
            db.add(nova_recorrencia)

        # 3. Commita tudo de uma vez. Se falhar, dá rollback em tudo.
        db.commit()
        db.refresh(nova_demanda)

        # 4. Chama o evento desacoplado (Kafka)
        payload_evento = {
            "id_empresa_comprador": nova_demanda.id_empresa_comprador,
            "id_produto": nova_demanda.id_produto,
            "quantidade_desejada": float(nova_demanda.quantidade_desejada),
            "preco_maximo": float(nova_demanda.preco_maximo) if nova_demanda.preco_maximo else None,
            "tipo_demanda": nova_demanda.is_recorrente,
            "prioridade": nova_demanda.prioridade
        }
        DemandaProducer.publicar_demanda_criada(nova_demanda.id_demanda, payload_evento)

        return nova_demanda
    
    @staticmethod
    def listar_demandas_da_empresa(db: Session, id_empresa: str):
        demandas = db.query(Demanda).filter(Demanda.id_empresa_comprador == id_empresa).order_by(desc(Demanda.data_criacao)).all()
        return demandas