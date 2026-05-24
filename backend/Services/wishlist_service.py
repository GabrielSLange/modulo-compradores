from sqlalchemy.orm import Session
from Models.wishlist_item_model import WishlistItem
from DTOs.Request.wishlist_create_dto import WishlistCreateDTO, WishlistConverterDTO
from DTOs.Response.wishlist_response_dto import WishlistResponseDTO
from DTOs.Request.demanda_create_dto import DemandaCreateDTO
from DTOs.Response.demanda_response_dto import DemandaResponseDTO
from Services.demanda_service import DemandaService

class WishlistService:
    @staticmethod
    def adicionar_item(db: Session, dto: WishlistCreateDTO, id_empresa: str, id_usuario: str) -> WishlistResponseDTO:
        novo_item = WishlistItem(
            id_empresa=id_empresa,
            id_usuario=id_usuario,
            id_produto=dto.id_produto,
            quantidade_desejada=dto.quantidade_desejada,
            preco_maximo=dto.preco_maximo,
            prioridade=dto.prioridade,
            observacoes=dto.observacoes,
            convertido_em_demanda=False
        )
        db.add(novo_item)
        db.commit()
        db.refresh(novo_item)
        return WishlistResponseDTO.model_validate(novo_item)

    @staticmethod
    def listar_itens_pendentes(db: Session, id_empresa: str) -> list[WishlistResponseDTO]:
        # Traz só os itens que ainda NÃO viraram demanda e são da empresa
        query = db.query(WishlistItem).filter(
            WishlistItem.convertido_em_demanda == False,
            WishlistItem.id_empresa == id_empresa
        )
        itens = query.all()
        return [WishlistResponseDTO.model_validate(i) for i in itens]

    @staticmethod
    def converter_em_demanda(db: Session, id_item: str, id_usuario: str, dto: WishlistConverterDTO, id_empresa: str) -> DemandaResponseDTO:
        # 1. Busca o item na wishlist validando a posse da empresa
        item = db.query(WishlistItem).filter(
            WishlistItem.id_item == id_item,
            WishlistItem.id_empresa == id_empresa
        ).first()
        if not item:
            raise ValueError("Item da wishlist não encontrado ou você não tem permissão.")
        if item.convertido_em_demanda:
            raise ValueError("Este item já foi convertido em demanda anteriormente.")

        # 2. Prepara o DTO da Demanda juntando os dados da Wishlist com os dados da requisição
        demanda_dto = DemandaCreateDTO(
            id_produto=str(item.id_produto),
            id_endereco_destino=str(dto.id_endereco_destino),
            quantidade_desejada=dto.quantidade_desejada,
            preco_maximo=float(item.preco_maximo) if item.preco_maximo is not None else None,
            prioridade=dto.prioridade,
            observacoes=item.observacoes,
            is_recorrente=False # Conversão simples não é recorrente por padrão
        )

        # 3. MÁGICA: Chama o serviço de Demanda (que salva no banco e dispara pro Kafka)
        nova_demanda = DemandaService.criar_demanda(db, demanda_dto, id_empresa_comprador=item.id_empresa, id_usuario_criador=id_usuario)

        # 4. Atualiza o status do item na wishlist com o link de rastreabilidade
        item.convertido_em_demanda = True
        item.id_demanda_gerada = nova_demanda.id # Agora acessa o .id do DTO, e não .id_demanda
        db.commit()

        return nova_demanda
