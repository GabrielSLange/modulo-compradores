from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from Models.demanda_model import Demanda
from Models.demanda_recorrencia_model import DemandaRecorrencia
from DTOs.Request.demanda_create_dto import DemandaCreateDTO
from DTOs.Response.demanda_response_dto import DemandaResponseDTO
from Events.Producers.demanda_producer import DemandaProducer
from Services.estoque_service import EstoqueService

class DemandaService:
    @staticmethod
    def criar_demanda(db: Session, dto: DemandaCreateDTO, id_empresa_comprador: str, id_usuario_criador: str) -> DemandaResponseDTO:
        # 1. Cria a Demanda (A Raiz)
        nova_demanda = Demanda(
            id_empresa_comprador=id_empresa_comprador,
            id_usuario_criador=id_usuario_criador,
            id_produto=dto.id_produto,
            id_endereco_destino=dto.id_endereco_destino,
            quantidade_desejada=dto.quantidade_desejada,
            preco_maximo=dto.preco_maximo,
            prioridade=dto.prioridade,
            is_recorrente=dto.is_recorrente,
            status="aberta",
            observacoes=dto.observacoes
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

        return DemandaResponseDTO.model_validate(nova_demanda)
    
    @staticmethod
    def listar_demandas_da_empresa(db: Session, id_empresa: str, is_pedido: Optional[bool] = None) -> list[DemandaResponseDTO]:
        query = db.query(Demanda).filter(Demanda.id_empresa_comprador == id_empresa)
        if is_pedido is not None:
            query = query.filter(Demanda.is_pedido == is_pedido)
        demandas = query.order_by(desc(Demanda.data_criacao)).all()
        return [DemandaResponseDTO.model_validate(d) for d in demandas]

    @staticmethod
    def atualizar_status(db: Session, id_demanda: str, novo_status: str, id_empresa_comprador: str) -> DemandaResponseDTO:
        demanda = db.query(Demanda).filter(
            Demanda.id_demanda == id_demanda,
            Demanda.id_empresa_comprador == id_empresa_comprador
        ).first()
        if not demanda:
            raise ValueError(f"Demanda {id_demanda} não encontrada ou você não tem permissão.")
        
        demanda.status = novo_status
        db.commit()
        db.refresh(demanda)
        
        # Se eh um pedido (is_pedido=true) e mudou de status, avisa pelo Kafka.
        # Demandas que ainda nao viraram pedido nao tem evento na doc oficial.
        if demanda.is_pedido:
            payload_evento = {
                "id_demanda": demanda.id_demanda,
                "id_empresa_comprador": demanda.id_empresa_comprador,
                "id_produto": demanda.id_produto,
                "status": novo_status
            }
            DemandaProducer.publicar_pedido_atualizado(demanda.id_demanda, payload_evento)

        return DemandaResponseDTO.model_validate(demanda)

    @staticmethod
    def promover_para_pedido(
        db: Session,
        fornecimento_db: Session,
        id_demanda: str,
        id_empresa_comprador: str,
    ) -> DemandaResponseDTO:
        demanda = db.query(Demanda).filter(
            Demanda.id_demanda == id_demanda,
            Demanda.id_empresa_comprador == id_empresa_comprador
        ).first()

        if not demanda:
            raise ValueError("Demanda não encontrada")

        if demanda.is_pedido:
            return DemandaResponseDTO.model_validate(demanda)

        if demanda.status == "cancelada":
            raise ValueError("Não é possível promover demanda cancelada para pedido")

        resultado_estoque = EstoqueService.validar_estoque(
            fornecimento_db=fornecimento_db,
            id_produto=demanda.id_produto,
            quantidade_desejada=float(demanda.quantidade_desejada),
        )

        if not resultado_estoque.valido:
            demanda.status = "aberta"
            db.commit()
            raise ValueError(
                "Nenhum fornecedor possui estoque suficiente para atender a quantidade desejada. "
                "A demanda permanece aberta."
            )

        demanda.is_pedido = True
        db.commit()
        db.refresh(demanda)

        payload_evento = {
            "id_demanda": demanda.id_demanda,
            "id_empresa_comprador": demanda.id_empresa_comprador,
            "id_produto": demanda.id_produto,
            "quantidade": float(demanda.quantidade_desejada),
            "preco_maximo": float(demanda.preco_maximo) if demanda.preco_maximo else None,
            "prioridade": demanda.prioridade,
            "id_fornecedor_apto": str(resultado_estoque.id_fornecedor_apto),
        }
        DemandaProducer.publicar_pedido_criado(demanda.id_demanda, payload_evento)

        return DemandaResponseDTO.model_validate(demanda)