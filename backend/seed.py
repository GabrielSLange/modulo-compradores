"""
seed.py - Popula o banco SQLite local com dados de exemplo.
Execute com o backend PARADO: python seed.py
"""
import sys
import io
# Garante UTF-8 no terminal Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import uuid

from datetime import datetime, timezone, timedelta
from Data.database import Base, engine, SessionLocal
from Models import (
    endereco_entrega_model,
    demanda_model,
    demanda_recorrencia_model,
    wishlist_item_model,
    produto_cache_model,
)

# ─── IDs fixos para facilitar testes ─────────────────────────────────────────

ID_EMPRESA   = "empresa-001"
ID_USUARIO   = "usuario-001"

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

# ─── Recria as tabelas ────────────────────────────────────────────────────────

print("🗑️  Recriando tabelas...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # ── 1. Produto Cache (normalmente alimentado pelo Kafka) ──────────────────
    print("📦 Inserindo produtos no cache...")
    db.add_all([
        produto_cache_model.ProdutoCache(
            id_produto=ID_PROD_1,
            codigo="NOTE-001",
            nome="Notebook Dell Inspiron 15",
            ativo=True,
            sincronizado_em=now,
        ),
        produto_cache_model.ProdutoCache(
            id_produto=ID_PROD_2,
            codigo="CADM-002",
            nome="Cadeira de Escritório Ergonômica",
            ativo=True,
            sincronizado_em=now,
        ),
        produto_cache_model.ProdutoCache(
            id_produto=ID_PROD_3,
            codigo="PAPE-003",
            nome="Papel A4 Resma 500 Folhas",
            ativo=True,
            sincronizado_em=now,
        ),
    ])

    # ── 2. Endereços de entrega ───────────────────────────────────────────────
    print("📍 Inserindo endereços...")
    db.add_all([
        endereco_entrega_model.EnderecoEntrega(
            id_endereco=ID_END_1,
            id_empresa=ID_EMPRESA,
            logradouro="Avenida Paulista",
            numero="1000",
            complemento="Andar 10",
            bairro="Bela Vista",
            cidade="São Paulo",
            estado="SP",
            cep="01310-100",
            ativo=True,
            criado_em=now - timedelta(days=30),
            atualizado_em=now,
        ),
        endereco_entrega_model.EnderecoEntrega(
            id_endereco=ID_END_2,
            id_empresa=ID_EMPRESA,
            logradouro="Rua XV de Novembro",
            numero="320",
            complemento=None,
            bairro="Centro",
            cidade="Curitiba",
            estado="PR",
            cep="80020-310",
            ativo=True,
            criado_em=now - timedelta(days=15),
            atualizado_em=now,
        ),
    ])

    # ── 3. Demandas ───────────────────────────────────────────────────────────
    print("📋 Inserindo demandas...")
    db.add_all([
        demanda_model.Demanda(
            id_demanda=ID_DEM_1,
            id_empresa_comprador=ID_EMPRESA,
            id_usuario_criador=ID_USUARIO,
            id_produto=ID_PROD_1,
            id_endereco_destino=ID_END_1,
            quantidade_desejada=5,
            preco_maximo=None,
            prioridade="alta",
            is_recorrente=False,
            status="aberta",
            data_criacao=now - timedelta(days=10),
            atualizado_em=now - timedelta(days=10),
        ),
        demanda_model.Demanda(
            id_demanda=ID_DEM_2,
            id_empresa_comprador=ID_EMPRESA,
            id_usuario_criador=ID_USUARIO,
            id_produto=ID_PROD_2,
            id_endereco_destino=ID_END_2,
            quantidade_desejada=10,
            preco_maximo=800.00,
            prioridade="media",
            is_recorrente=True,
            status="em_negociacao",
            data_criacao=now - timedelta(days=5),
            atualizado_em=now - timedelta(days=2),
        ),
        demanda_model.Demanda(
            id_demanda=ID_DEM_3,
            id_empresa_comprador=ID_EMPRESA,
            id_usuario_criador=ID_USUARIO,
            id_produto=ID_PROD_3,
            id_endereco_destino=ID_END_1,
            quantidade_desejada=50,
            preco_maximo=None,
            prioridade="baixa",
            is_recorrente=False,
            status="atendida",
            data_criacao=now - timedelta(days=20),
            atualizado_em=now - timedelta(days=1),
        ),
    ])

    # ── 4. Wishlist ───────────────────────────────────────────────────────────
    print("⭐ Inserindo wishlist...")
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
            criado_em=now - timedelta(days=3),
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
            criado_em=now - timedelta(days=7),
            atualizado_em=now - timedelta(days=5),
        ),
    ])

    db.commit()
    print("\n✅ Seed concluído com sucesso!")
    print(f"   🏢 Empresa ID  : {ID_EMPRESA}")
    print(f"   👤 Usuário ID  : {ID_USUARIO}")
    print(f"   📦 Produtos    : 3")
    print(f"   📍 Endereços   : 2")
    print(f"   📋 Demandas    : 3  (aberta / em_negociacao / atendida)")
    print(f"   ⭐ Wishlist    : 2  (1 pendente, 1 convertida)")

except Exception as e:
    db.rollback()
    print(f"\n❌ Erro durante o seed: {e}")
    raise
finally:
    db.close()
