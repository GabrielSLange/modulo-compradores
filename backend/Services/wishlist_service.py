from sqlalchemy.orm import Session
from Models.wishlist_item_model import WishlistItem
from DTOs.Request.wishlist_create_dto import WishlistCreateDTO, WishlistConverterDTO
from DTOs.Response.wishlist_response_dto import WishlistResponseDTO
from DTOs.Request.demanda_create_dto import DemandaCreateDTO
from DTOs.Response.demanda_response_dto import DemandaResponseDTO
from Services.demanda_service import DemandaService

class WishlistService:
    @staticmethod
    def adicionar_item(db: Session, dto: WishlistCreateDTO) -> WishlistResponseDTO:
        novo_item = WishlistItem(
            id_empresa=dto.id_empresa,
            id_usuario=dto.id_usuario,
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
    def listar_itens_pendentes(db: Session, id_empresa: str | None = None) -> list[WishlistResponseDTO]:
        # TODO: quando JWT for implementado, id_empresa sempre virá do token — remover o None.
        # Traz só os itens que ainda NÃO viraram demanda
        query = db.query(WishlistItem).filter(WishlistItem.convertido_em_demanda == False)
        if id_empresa:
            query = query.filter(WishlistItem.id_empresa == id_empresa)
        itens = query.all()
        return [WishlistResponseDTO.model_validate(i) for i in itens]

    @staticmethod
    def converter_em_demanda(db: Session, id_item: str, id_usuario: str, dto: WishlistConverterDTO) -> DemandaResponseDTO:
        # 1. Busca o item na wishlist
        item = db.query(WishlistItem).filter(WishlistItem.id_item == id_item).first()
        if not item:
            raise ValueError("Item da wishlist não encontrado.")
        if item.convertido_em_demanda:
            raise ValueError("Este item já foi convertido em demanda anteriormente.")

        # 2. Prepara o DTO da Demanda juntando os dados da Wishlist com os dados da requisição
        demanda_dto = DemandaCreateDTO(
            id_empresa_comprador=item.id_empresa,
            id_usuario_criador=id_usuario, # Quem está clicando no botão de converter
            id_produto=item.id_produto,
            id_endereco_destino=dto.id_endereco_destino,
            quantidade_desejada=dto.quantidade_desejada,
            preco_maximo=item.preco_maximo,
            prioridade=dto.prioridade,
            observacoes=item.observacoes,
            is_recorrente=False # Conversão simples não é recorrente por padrão
        )

        # 3. MÁGICA: Chama o serviço de Demanda (que salva no banco e dispara pro Kafka)
        # O serviço de demanda já retorna um DemandaResponseDTO com a refatoração, 
        # então apenas recebemos e retornamos.
        nova_demanda = DemandaService.criar_demanda(db, demanda_dto)

        # 4. Atualiza o status do item na wishlist com o link de rastreabilidade
        item.convertido_em_demanda = True
        item.id_demanda_gerada = nova_demanda.id # Agora acessa o .id do DTO, e não .id_demanda
        db.commit()

        return nova_demanda