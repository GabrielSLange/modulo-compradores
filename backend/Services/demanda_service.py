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
            import uuid
            from sqlalchemy import text
            
            is_sqlite = db.bind.name == "sqlite"
            
            if is_sqlite:
                processo_id_final = str(uuid.uuid4())
                fornecimento_id_final = str(uuid.uuid4())
            else:
                # 1. Resolve processo_id (Garante existência na tabela processo_negociacao)
                processo_id_final = None
                try:
                    res = db.execute(text("SELECT id FROM portal_b2b.processo_negociacao LIMIT 1")).fetchone()
                    if res:
                        processo_id_final = str(res[0])
                    else:
                        dummy_proc_id = str(uuid.uuid4())
                        db.execute(text(
                            "INSERT INTO portal_b2b.processo_negociacao (id, produto_id, modo, status) "
                            "VALUES (:id, :prod_id, 'direto', 'ABERTO')"
                        ), {"id": dummy_proc_id, "prod_id": demanda.id_produto})
                        processo_id_final = dummy_proc_id
                except Exception:
                    processo_id_final = str(uuid.uuid4())

                # 2. Resolve fornecimento_id (Garante existência na tabela fornecimento e dependências)
                fornecimento_id_final = demanda.id_fornecimento
                if not fornecimento_id_final:
                    try:
                        from uuid import UUID as PyUUID
                        from Models.fornecimento_model import Fornecimento
                        prod_uuid = PyUUID(str(demanda.id_produto))
                        f = fornecimento_db.query(Fornecimento).filter(
                            Fornecimento.produto_id == prod_uuid,
                            Fornecimento.empresa_fornecedor_id == PyUUID(str(id_fornecedor_final)),
                            Fornecimento.ativo.is_(True)
                        ).first()
                        if f:
                            fornecimento_id_final = str(f.id)
                        else:
                            f_any = fornecimento_db.query(Fornecimento).filter(
                                Fornecimento.produto_id == prod_uuid
                            ).first()
                            if f_any:
                                fornecimento_id_final = str(f_any.id)
                    except Exception:
                        pass

                if not fornecimento_id_final:
                    try:
                        # Busca ou insere endereço para o fornecedor
                        end_res = db.execute(text(
                            "SELECT id FROM portal_b2b.endereco "
                            "WHERE empresa_id = :emp_id LIMIT 1"
                        ), {"emp_id": id_fornecedor_final}).fetchone()
                        end_id = str(end_res[0]) if end_res else None
                        
                        if not end_id:
                            end_any = db.execute(text("SELECT id FROM portal_b2b.endereco LIMIT 1")).fetchone()
                            end_id = str(end_any[0]) if end_any else None
                            
                        if not end_id:
                            dummy_end_id = str(uuid.uuid4())
                            db.execute(text(
                                "INSERT INTO portal_b2b.endereco (id, empresa_id, cidade, estado, cep) "
                                "VALUES (:id, :emp_id, 'Goiania', 'GO', '74000000')"
                            ), {"id": dummy_end_id, "emp_id": id_fornecedor_final})
                            end_id = dummy_end_id

                        # Insere o fornecimento
                        dummy_forn_id = str(uuid.uuid4())
                        db.execute(text(
                            "INSERT INTO portal_b2b.fornecimento (id, empresa_fornecedor_id, produto_id, "
                            "endereco_origem_id, preco_unitario, quantidade_disponivel) "
                            "VALUES (:id, :forn_id, :prod_id, :end_id, 100.0, 999.0)"
                        ), {
                            "id": dummy_forn_id,
                            "forn_id": id_fornecedor_final,
                            "prod_id": demanda.id_produto,
                            "end_id": end_id
                        })
                        fornecimento_id_final = dummy_forn_id
                    except Exception:
                        fornecimento_id_final = str(uuid.uuid4())

            # 3. Insere o registro na tabela pedido
            valor_total_pedido = valor_total or (float(demanda.quantidade_desejada) * (preco_final or 150.00))
            if valor_total_pedido <= 0:
                valor_total_pedido = 150.00

            novo_pedido = Pedido(
                id=demanda.id_demanda,
                processo_id=processo_id_final,
                empresa_comprador_id=demanda.id_empresa_comprador,
                empresa_fornecedor_id=id_fornecedor_final,
                fornecimento_id=fornecimento_id_final,
                valor_total=valor_total_pedido,
                status="atendida"
            )
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

    @staticmethod
    def simular_pedido_teste(
        db: Session,
        id_demanda: str,
        id_empresa_comprador: str,
        payload: dict,
        token: str
    ) -> DemandaResponseDTO:
        import uuid
        from Models.pedido_model import Pedido
        
        demanda = db.query(Demanda).filter(
            Demanda.id_demanda == id_demanda,
            Demanda.id_empresa_comprador == id_empresa_comprador
        ).first()

        if not demanda:
            raise ValueError("Demanda não encontrada ou permissão negada.")

        # Tenta achar um fornecedor válido cadastrado na tabela 'empresa' para evitar violação de FK
        id_fornecedor_final = payload.get("id_fornecedor")
        if not id_fornecedor_final:
            from Data.fornecimento_database import FornecimentoSessionLocal
            from Models.fornecimento_model import Fornecimento
            try:
                from uuid import UUID as PyUUID
                prod_uuid = PyUUID(str(demanda.id_produto))
                with FornecimentoSessionLocal() as f_db:
                    f = f_db.query(Fornecimento).filter(Fornecimento.produto_id == prod_uuid).first()
                    if f:
                        id_fornecedor_final = str(f.empresa_fornecedor_id)
                    else:
                        f_any = f_db.query(Fornecimento).first()
                        if f_any:
                            id_fornecedor_final = str(f_any.empresa_fornecedor_id)
            except Exception:
                pass

        if not id_fornecedor_final:
            try:
                from sqlalchemy import text
                result = db.execute(text("SELECT id FROM portal_b2b.empresa LIMIT 1")).fetchone()
                if result:
                    id_fornecedor_final = str(result[0])
            except Exception:
                pass

        if not id_fornecedor_final:
            id_fornecedor_final = demanda.id_empresa_comprador

        # Força campos de pedido
        demanda.is_pedido = True
        demanda.status = "atendida"
        demanda.id_fornecedor = id_fornecedor_final
        demanda.preco_final = payload.get("preco_final") or 150.00
        demanda.valor_total = payload.get("valor_total") or (float(demanda.quantidade_desejada) * 150.00)
        demanda.tipo_transporte = payload.get("tipo_transporte") or "RODOVIARIO"
        
        # CEP destino
        cep_dest = payload.get("cep_destino")
        if not cep_dest and demanda.endereco:
            cep_dest = demanda.endereco.cep
        if cep_dest:
            cep_dest = cep_dest.replace("-", "").replace(" ", "")
        demanda.cep_destino = cep_dest or "01001000"
        
        demanda.cep_origem = payload.get("cep_origem") or "74000000"
        
        peso = payload.get("peso_carga")
        if peso is None:
            demanda.peso_carga = float(demanda.quantidade_desejada) * 1.5
        else:
            demanda.peso_carga = peso

        # Insere na tabela shared 'pedido'
        pedido_existente = db.query(Pedido).filter(Pedido.id == demanda.id_demanda).first()
        if not pedido_existente:
            from sqlalchemy import text
            is_sqlite = db.bind.name == "sqlite"
            
            if is_sqlite:
                processo_id_final = str(uuid.uuid4())
                fornecimento_id_final = str(uuid.uuid4())
            else:
                # 1. Resolve processo_id
                processo_id_final = None
                try:
                    res = db.execute(text("SELECT id FROM portal_b2b.processo_negociacao LIMIT 1")).fetchone()
                    if res:
                        processo_id_final = str(res[0])
                    else:
                        dummy_proc_id = str(uuid.uuid4())
                        db.execute(text(
                            "INSERT INTO portal_b2b.processo_negociacao (id, produto_id, modo, status) "
                            "VALUES (:id, :prod_id, 'direto', 'ABERTO')"
                        ), {"id": dummy_proc_id, "prod_id": demanda.id_produto})
                        processo_id_final = dummy_proc_id
                except Exception:
                    processo_id_final = str(uuid.uuid4())

                # 2. Resolve fornecimento_id
                fornecimento_id_final = None
                try:
                    from Data.fornecimento_database import FornecimentoSessionLocal
                    from Models.fornecimento_model import Fornecimento
                    from uuid import UUID as PyUUID
                    prod_uuid = PyUUID(str(demanda.id_produto))
                    with FornecimentoSessionLocal() as f_db:
                        f = f_db.query(Fornecimento).filter(
                            Fornecimento.produto_id == prod_uuid,
                            Fornecimento.empresa_fornecedor_id == PyUUID(str(id_fornecedor_final)),
                            Fornecimento.ativo.is_(True)
                        ).first()
                        if f:
                            fornecimento_id_final = str(f.id)
                        else:
                            f_any = f_db.query(Fornecimento).filter(
                                Fornecimento.produto_id == prod_uuid
                            ).first()
                            if f_any:
                                fornecimento_id_final = str(f_any.id)
                except Exception:
                    pass

                if not fornecimento_id_final:
                    try:
                        # Busca ou insere endereço para o fornecedor
                        end_res = db.execute(text(
                            "SELECT id FROM portal_b2b.endereco "
                            "WHERE empresa_id = :emp_id LIMIT 1"
                        ), {"emp_id": id_fornecedor_final}).fetchone()
                        end_id = str(end_res[0]) if end_res else None
                        
                        if not end_id:
                            end_any = db.execute(text("SELECT id FROM portal_b2b.endereco LIMIT 1")).fetchone()
                            end_id = str(end_any[0]) if end_any else None
                            
                        if not end_id:
                            dummy_end_id = str(uuid.uuid4())
                            db.execute(text(
                                "INSERT INTO portal_b2b.endereco (id, empresa_id, cidade, estado, cep) "
                                "VALUES (:id, :emp_id, 'Goiania', 'GO', '74000000')"
                            ), {"id": dummy_end_id, "emp_id": id_fornecedor_final})
                            end_id = dummy_end_id

                        # Insere o fornecimento
                        dummy_forn_id = str(uuid.uuid4())
                        db.execute(text(
                            "INSERT INTO portal_b2b.fornecimento (id, empresa_fornecedor_id, produto_id, "
                            "endereco_origem_id, preco_unitario, quantidade_disponivel) "
                            "VALUES (:id, :forn_id, :prod_id, :end_id, 100.0, 999.0)"
                        ), {
                            "id": dummy_forn_id,
                            "forn_id": id_fornecedor_final,
                            "prod_id": demanda.id_produto,
                            "end_id": end_id
                        })
                        fornecimento_id_final = dummy_forn_id
                    except Exception:
                        fornecimento_id_final = str(uuid.uuid4())

            # 3. Insere o registro na tabela pedido
            valor_total_pedido = demanda.valor_total
            if not valor_total_pedido or valor_total_pedido <= 0:
                valor_total_pedido = 150.00

            novo_pedido = Pedido(
                id=demanda.id_demanda,
                processo_id=processo_id_final,
                empresa_comprador_id=demanda.id_empresa_comprador,
                empresa_fornecedor_id=id_fornecedor_final,
                fornecimento_id=fornecimento_id_final,
                valor_total=valor_total_pedido,
                status="atendida"
            )
            db.add(novo_pedido)
            db.flush()

        db.commit()
        db.refresh(demanda)

        # Chama a API de Logística
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
                    else:
                        logistica_logger.error(f"Erro ao criar solicitação na Logística: {resp.status_code}, {resp.text}")
            except Exception as e:
                logistica_logger.exception(f"Falha ao conectar com o serviço de Logística: {e}")

        # Publica evento de pedido_criado no Kafka
        payload_evento = {
            "pedido_id": demanda.id_demanda,
            "tipo_transporte": demanda.tipo_transporte,
            "peso_carga": float(demanda.peso_carga) if demanda.peso_carga else 0.0,
            "cep_origem": demanda.cep_origem or "74000000",
            "cep_destino": demanda.cep_destino or "01001000",
            "id_demanda": demanda.id_demanda,
            "id_empresa_comprador": demanda.id_empresa_comprador,
            "id_produto": demanda.id_produto,
            "quantidade": float(demanda.quantidade_desejada),
            "preco_unitario_final": float(demanda.preco_final) if demanda.preco_final else None,
            "valor_total": float(demanda.valor_total) if demanda.valor_total else None,
            "id_fornecedor": demanda.id_fornecedor,
        }
        from Events.Producers.demanda_producer import DemandaProducer
        DemandaProducer.publicar_pedido_criado(demanda.id_demanda, payload_evento)

        return DemandaResponseDTO.model_validate(demanda)