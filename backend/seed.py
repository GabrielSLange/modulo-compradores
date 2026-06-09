import sys
import io
import uuid
from datetime import datetime, timezone, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from Data.database import Base, engine, SessionLocal
from Models import (
    endereco_entrega_model,
    demanda_model,
    demanda_recorrencia_model,
    wishlist_item_model,
    produto_cache_model,
    pedido_model,
)

ID_EMPRESA   = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
ID_USUARIO   = "550e8400-e29b-41d4-a716-446655440000"

ID_PROD_1    = str(uuid.uuid4())
ID_PROD_2    = str(uuid.uuid4())
ID_PROD_3    = str(uuid.uuid4())

ID_END_1     = str(uuid.uuid4())
ID_END_2     = str(uuid.uuid4())

ID_DEM_1     = str(uuid.uuid4())
ID_DEM_2     = str(uuid.uuid4())
ID_DEM_3     = str(uuid.uuid4())

ID_WISH_1    = str(uuid.uuid4())
ID_WISH_2    = str(uuid.uuid4())

now = datetime.now(timezone.utc)

print("Recriando as tabelas no banco de dados...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    print("Inserindo produtos no cache...")
    db.add_all([
        produto_cache_model.ProdutoCache(
            id_produto=ID_PROD_1,
            codigo="NOTE-001",
            nome="Notebook Dell Inspiron",
            ativo=True,
            sincronizado_em=now
        ),
        produto_cache_model.ProdutoCache(
            id_produto=ID_PROD_2,
            codigo="MON-002",
            nome="Monitor LG 29 Ultrawide",
            ativo=True,
            sincronizado_em=now
        ),
        produto_cache_model.ProdutoCache(
            id_produto=ID_PROD_3,
            codigo="TEC-003",
            nome="Teclado Mecânico Keychron",
            ativo=False,
            sincronizado_em=now
        ),
    ])

    print("Inserindo enderecos de entrega...")
    db.add_all([
        endereco_entrega_model.EnderecoEntrega(
            id_endereco=ID_END_1,
            id_empresa=ID_EMPRESA,
            apelido="Sede Matriz",
            logradouro="Avenida Paulista",
            numero="1000",
            complemento="Andar 5",
            bairro="Bela Vista",
            cidade="Sao Paulo",
            estado="SP",
            cep="01310100",
            ativo=True,
        ),
        endereco_entrega_model.EnderecoEntrega(
            id_endereco=ID_END_2,
            id_empresa=ID_EMPRESA,
            apelido="Filial Goiania",
            logradouro="Avenida T-63",
            numero="320",
            complemento="Sala 12",
            bairro="Setor Bueno",
            cidade="Goiania",
            estado="GO",
            cep="74230100",
            ativo=True,
        ),
    ])

    print("Inserindo demandas...")
    db.add_all([
        demanda_model.Demanda(
            id_demanda=ID_DEM_1,
            id_empresa_comprador=ID_EMPRESA,
            id_usuario_criador=ID_USUARIO,
            id_produto=ID_PROD_1,
            id_endereco_destino=ID_END_1,
            quantidade_desejada=10,
            prioridade="alta",
            status="aberta",
            observacoes="Aguardando aprovacao de orcamento",
            is_recorrente=False,
            data_criacao=now - timedelta(days=2),
            atualizado_em=now - timedelta(days=2),
        ),
        demanda_model.Demanda(
            id_demanda=ID_DEM_2,
            id_empresa_comprador=ID_EMPRESA,
            id_usuario_criador=ID_USUARIO,
            id_produto=ID_PROD_2,
            id_endereco_destino=ID_END_2,
            quantidade_desejada=5,
            prioridade="media",
            status="em_negociacao",
            observacoes=None,
            is_recorrente=True,
            data_criacao=now - timedelta(days=5),
            atualizado_em=now - timedelta(days=1),
        ),
        demanda_model.Demanda(
            id_demanda=ID_DEM_3,
            id_empresa_comprador=ID_EMPRESA,
            id_usuario_criador=ID_USUARIO,
            id_produto=ID_PROD_3,
            id_endereco_destino=None,
            quantidade_desejada=2,
            prioridade="baixa",
            status="atendida",
            observacoes="Pedido finalizado",
            is_recorrente=False,
            is_pedido=True,
            data_criacao=now - timedelta(days=10),
            atualizado_em=now - timedelta(days=8),
        ),
    ])

    print("Inserindo configuracoes de recorrencia...")
    db.add_all([
        demanda_recorrencia_model.DemandaRecorrencia(
            id_recorrencia=str(uuid.uuid4()),
            id_demanda=ID_DEM_2,
            frequencia="mensal",
            quantidade_por_periodo=5,
            data_inicio=now.date(),
            data_fim=None,
            dia_preferencial="15",
            ativa=True
        )
    ])

    print("Inserindo itens na wishlist...")
    db.add_all([
        wishlist_item_model.WishlistItem(
            id_item=ID_WISH_1,
            id_empresa=ID_EMPRESA,
            id_usuario=ID_USUARIO,
            id_produto=ID_PROD_1,
            quantidade_desejada=2,
            preco_maximo=3500.00,
            prioridade="alta",
            observacoes="Preferencialmente com SSD 512GB",
            convertido_em_demanda=False,
            id_demanda_gerada=None,
            data_criacao=now - timedelta(days=3),
            atualizado_em=now - timedelta(days=3),
        ),
        wishlist_item_model.WishlistItem(
            id_item=ID_WISH_2,
            id_empresa=ID_EMPRESA,
            id_usuario=ID_USUARIO,
            id_produto=ID_PROD_2,
            quantidade_desejada=5,
            preco_maximo=None,
            prioridade="media",
            observacoes=None,
            convertido_em_demanda=True,
            id_demanda_gerada=ID_DEM_2,
            data_criacao=now - timedelta(days=7),
            atualizado_em=now - timedelta(days=5),
        ),
    ])

    db.commit()
    print("Seed concluido com sucesso!")
    print(f"Empresa ID  : {ID_EMPRESA}")
    print(f"Usuario ID  : {ID_USUARIO}")

except Exception as e:
    db.rollback()
    print(f"Erro ao executar seed: {e}")
finally:
    db.close()