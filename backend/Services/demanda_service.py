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
        # Resolve id_fornecimento automaticamente se não vier no DTO
        id_fornecimento_final = getattr(dto, "id_fornecimento", None)
        if not id_fornecimento_final:
            from uuid import UUID
            from Data.fornecimento_database import FornecimentoSessionLocal
            from Models.fornecimento_model import Fornecimento
            try:
                prod_uuid = UUID(str(dto.id_produto))
                with FornecimentoSessionLocal() as fornecimento_db:
                    # 1. Tenta achar um fornecimento ativo com estoque suficiente
                    fornecedor_apto = (
                        fornecimento_db.query(Fornecimento)
                        .filter(
                            Fornecimento.produto_id == prod_uuid,
                            Fornecimento.quantidade_disponivel >= dto.quantidade_desejada,
                            Fornecimento.ativo.is_(True),
                        )
                        .first()
                    )
                    if fornecedor_apto:
                        id_fornecimento_final = str(fornecedor_apto.id)
                    else:
                        # 2. Fallback: Pega qualquer fornecimento ativo deste produto
                        qualquer_fornecedor = (
                            fornecimento_db.query(Fornecimento)
                            .filter(
                                Fornecimento.produto_id == prod_uuid,
                                Fornecimento.ativo.is_(True),
                            )
                            .first()
                        )
                        if qualquer_fornecedor:
                            id_fornecimento_final = str(qualquer_fornecedor.id)
            except ValueError:
                pass

        # 1. Cria a Demanda (A Raiz)
        nova_demanda = Demanda(
            id_empresa_comprador=id_empresa_comprador,
            id_usuario_criador=id_usuario_criador,
            id_produto=dto.id_produto,
            id_fornecimento=id_fornecimento_final,
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
            "prioridade": nova_demanda.prioridade,
            "id_fornecimento": nova_demanda.id_fornecimento,
            "status": nova_demanda.status
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

        if novo_status == "cancelada":
            payload_cancelamento = {
                "id_empresa_comprador": demanda.id_empresa_comprador,
                "id_produto": demanda.id_produto,
                "quantidade_desejada": float(demanda.quantidade_desejada),
                "preco_maximo": float(demanda.preco_maximo) if demanda.preco_maximo else None,
                "tipo_demanda": demanda.is_recorrente,
                "prioridade": demanda.prioridade,
                "id_fornecimento": demanda.id_fornecimento,
                "status": "cancelada"
            }
            DemandaProducer.publicar_demanda_cancelada(demanda.id_demanda, payload_cancelamento)

        return DemandaResponseDTO.model_validate(demanda)

    @staticmethod
    def promover_para_pedido(
        db: Session,
        fornecimento_db: Session,
        id_demanda: str,
        id_empresa_comprador: str,
        id_fornecedor: Optional[str] = None,
        preco_final: Optional[float] = None,
        valor_total: Optional[float] = None,
        tipo_transporte: Optional[str] = "RODOVIARIO",
        peso_carga: Optional[float] = None,
        cep_origem: Optional[str] = None,
        cep_destino: Optional[str] = None,
        token: Optional[str] = None,
    ) -> DemandaResponseDTO:
        demanda = db.query(Demanda).filter(
            Demanda.id_demanda == id_demanda,
            Demanda.id_empresa_comprador == id_empresa_comprador
        ).first()

        if not demanda:
            raise ValueError("Demanda não encontrada")

        if demanda.is_pedido and demanda.id_fornecedor:
            return DemandaResponseDTO.model_validate(demanda)

        if demanda.status == "cancelada":
            raise ValueError("Não é possível promover demanda cancelada para pedido")

        # Se id_fornecedor não foi fornecido (ex: promoção manual via API REST),
        # valida o estoque na base de fornecimento.
        if not id_fornecedor:
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
            id_fornecedor_final = str(resultado_estoque.id_fornecedor_apto)
        else:
            id_fornecedor_final = id_fornecedor

        # Atualiza campos da demanda para convertê-la em pedido
        demanda.is_pedido = True
        demanda.status = "atendida"
        demanda.id_fornecedor = id_fornecedor_final
        demanda.preco_final = preco_final
        demanda.valor_total = valor_total
        demanda.tipo_transporte = tipo_transporte or "RODOVIARIO"

        # Resolve CEP de destino a partir do endereço cadastrado se não fornecido
        cep_destino_final = cep_destino
        if not cep_destino_final and demanda.endereco:
            cep_destino_final = demanda.endereco.cep
            if cep_destino_final:
                cep_destino_final = cep_destino_final.replace("-", "").replace(" ", "")

        demanda.cep_destino = cep_destino_final
        demanda.cep_origem = cep_origem

        # Se o peso_carga não foi fornecido, estima-se 1kg por item como fallback
        if peso_carga is None:
            demanda.peso_carga = float(demanda.quantidade_desejada) * 1.0
        else:
            demanda.peso_carga = peso_carga

        # Garante a existência do registro na tabela 'pedido' para evitar violação de FK na Logística
        from Models.pedido_model import Pedido
        pedido_existente = db.query(Pedido).filter(Pedido.id == demanda.id_demanda).first()
        if not pedido_existente:
            novo_pedido = Pedido(id=demanda.id_demanda, status="atendida")
            db.add(novo_pedido)
            db.flush()

        db.commit()
        db.refresh(demanda)

        # Chamada REST para a Logística para criar a solicitação de frete
        if token:
            import httpx
            import os
            import logging
            
            logistica_logger = logging.getLogger("modulo-compradores.logistica")
            logistica_url = os.getenv("LOGISTICA_API_URL", "http://34.8.17.245/api/logistica")
            url_iniciar = f"{logistica_url}/demo-iniciar-cotacao"
            headers = {"Authorization": f"Bearer {token}"}
            
            payload_logistica = {
                "pedido_id": demanda.id_demanda,
                "tipo_transporte": demanda.tipo_transporte or "RODOVIARIO",
                "cep_origem": demanda.cep_origem or "74000000",
                "cep_destino": demanda.cep_destino or "01001000",
                "peso_carga": float(demanda.peso_carga) if demanda.peso_carga else 0.0
            }
            
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url_iniciar, json=payload_logistica, headers=headers)
                    if resp.status_code == 201:
                        resp_data = resp.json()
                        solicitacao_id = resp_data.get("id")
                        if solicitacao_id:
                            demanda.id_solicitacao_frete = str(solicitacao_id)
                            db.commit()
                            db.refresh(demanda)
                            logistica_logger.info(f"Solicitação de frete criada na Logística: ID {solicitacao_id} para demanda {demanda.id_demanda}")
                    else:
                        logistica_logger.error(f"Erro ao criar solicitação na Logística. Status: {resp.status_code}, Detalhe: {resp.text}")
            except Exception as e:
                logistica_logger.exception(f"Falha ao conectar com o serviço de Logística para criar solicitação: {e}")

        # Monta o payload conforme exigências da Equipe de Logística (pedido_criado)
        payload_evento = {
            "pedido_id": demanda.id_demanda,  # UUID esperado pela logística
            "tipo_transporte": demanda.tipo_transporte,
            "peso_carga": float(demanda.peso_carga) if demanda.peso_carga else 0.0,
            "cep_origem": demanda.cep_origem or "74000000",
            "cep_destino": demanda.cep_destino or "01001000",
            
            # Propriedades de compatibilidade interna para módulo de compradores
            "id_demanda": demanda.id_demanda,
            "id_empresa_comprador": demanda.id_empresa_comprador,
            "id_produto": demanda.id_produto,
            "quantidade": float(demanda.quantidade_desejada),
            "preco_unitario_final": float(demanda.preco_final) if demanda.preco_final else None,
            "valor_total": float(demanda.valor_total) if demanda.valor_total else None,
            "id_fornecedor": demanda.id_fornecedor,
        }
        DemandaProducer.publicar_pedido_criado(demanda.id_demanda, payload_evento)

        return DemandaResponseDTO.model_validate(demanda)

    @staticmethod
    def obter_cotacoes_logistica(id_demanda: str, token: str) -> list:
        import os
        import httpx
        from Data.database import SessionLocal
        
        # Busca o id_solicitacao_frete no banco
        with SessionLocal() as db:
            demanda = db.query(Demanda).filter(Demanda.id_demanda == id_demanda).first()
            id_solicitacao = demanda.id_solicitacao_frete if (demanda and demanda.id_solicitacao_frete) else None
            
        if not id_solicitacao:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"id_solicitacao_frete não encontrado para demanda {id_demanda}. Usando id_demanda como fallback.")
            id_solicitacao = id_demanda
            
        logistica_url = os.getenv("LOGISTICA_API_URL", "http://34.8.17.245/api/logistica")
        url = f"{logistica_url}/solicitacoes/{id_solicitacao}/cotacoes"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)
                if response.status_code == 404:
                    return []
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise ValueError(f"Erro na API de Logística: {e.response.text or e}")
        except Exception as e:
            raise RuntimeError(f"Falha de conexão com o serviço de Logística: {str(e)}")

    @staticmethod
    def contratar_frete_logistica(
        db: Session,
        id_demanda: str,
        id_empresa_comprador: str,
        cotacao_id: str,
        token: str
    ) -> DemandaResponseDTO:
        import os
        import httpx
        
        demanda = db.query(Demanda).filter(
            Demanda.id_demanda == id_demanda,
            Demanda.id_empresa_comprador == id_empresa_comprador
        ).first()
        
        if not demanda:
            raise ValueError("Demanda não encontrada ou você não tem permissão.")
            
        if not demanda.is_pedido:
            raise ValueError("Essa demanda ainda não foi promovida a pedido (não possui fornecedor ou lance fechado).")
            
        id_solicitacao = demanda.id_solicitacao_frete if demanda.id_solicitacao_frete else id_demanda
        logistica_url = os.getenv("LOGISTICA_API_URL", "http://34.8.17.245/api/logistica")
        url = f"{logistica_url}/demo-contratar-frete"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "solicitacao_id": id_solicitacao,
            "cotacao_id": cotacao_id
        }
        
        # Obtém o valor do frete antes de contratar para salvar em nosso banco local
        valor_frete = None
        try:
            cotacoes = DemandaService.obter_cotacoes_logistica(id_demanda, token)
            for c in cotacoes:
                if c.get("id") == cotacao_id:
                    valor_frete = float(c.get("valor"))
                    break
        except Exception:
            pass
            
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                raise ValueError("Este frete já foi contratado ou a solicitação já foi processada.")
            raise ValueError(f"Erro ao contratar frete na API de Logística: {e.response.text or e}")
        except Exception as e:
            raise RuntimeError(f"Falha de conexão ao contratar frete na Logística: {str(e)}")
            
        demanda.id_frete_selecionado = cotacao_id
        if valor_frete is not None:
            demanda.valor_frete = valor_frete
        demanda.status_frete = "SELECIONADO"
        
        db.commit()
        db.refresh(demanda)
        
        return DemandaResponseDTO.model_validate(demanda)