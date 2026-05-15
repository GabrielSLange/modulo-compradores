from sqlalchemy.orm import Session
from Models.endereco_entrega_model import EnderecoEntrega
from DTOs.Request.endereco_create_dto import EnderecoCreateDTO
from DTOs.Response.endereco_response_dto import EnderecoResponseDTO

class EnderecoService:
    @staticmethod
    def criar_endereco(db: Session, dto: EnderecoCreateDTO, id_empresa: str) -> EnderecoResponseDTO:
        novo_endereco = EnderecoEntrega(
            id_empresa=id_empresa,
            apelido=dto.apelido,
            logradouro=dto.logradouro,
            numero=dto.numero,
            complemento=dto.complemento,
            bairro=dto.bairro,
            cidade=dto.cidade,
            estado=dto.estado,
            cep=dto.cep,
            latitude=dto.latitude,
            longitude=dto.longitude,
            ativo=True
        )
        db.add(novo_endereco)
        db.commit()
        db.refresh(novo_endereco)
        return EnderecoResponseDTO.model_validate(novo_endereco)

    @staticmethod
    def atualizar_endereco(db: Session, id_endereco: str, dto: EnderecoCreateDTO, id_empresa: str) -> EnderecoResponseDTO | None:
        endereco = db.query(EnderecoEntrega).filter(
            EnderecoEntrega.id_endereco == id_endereco,
            EnderecoEntrega.id_empresa == id_empresa,
            EnderecoEntrega.ativo.is_(True)
        ).first()

        if not endereco:
            return None

        endereco.apelido = dto.apelido
        endereco.logradouro = dto.logradouro
        endereco.numero = dto.numero
        endereco.complemento = dto.complemento
        endereco.bairro = dto.bairro
        endereco.cidade = dto.cidade
        endereco.estado = dto.estado
        endereco.cep = dto.cep
        endereco.latitude = dto.latitude
        endereco.longitude = dto.longitude

        db.commit()
        db.refresh(endereco)
        return EnderecoResponseDTO.model_validate(endereco)

    @staticmethod
    def listar_enderecos_da_empresa(db: Session, id_empresa: str) -> list[EnderecoResponseDTO]:
        query = db.query(EnderecoEntrega).filter(
            EnderecoEntrega.ativo.is_(True),
            EnderecoEntrega.id_empresa == id_empresa
        )
        return [EnderecoResponseDTO.model_validate(e) for e in query.all()]

    @staticmethod
    def deletar_endereco_soft(db: Session, id_endereco: str, id_empresa: str) -> bool | None:
        # Busca o endereço garantindo que ele pertence à empresa que está pedindo a exclusão
        endereco = db.query(EnderecoEntrega).filter(
            EnderecoEntrega.id_endereco == id_endereco,
            EnderecoEntrega.id_empresa == id_empresa
        ).first()

        if not endereco:
            return None # Retorna None para o Controller tratar com erro 404

        # Realiza o Soft Delete
        endereco.ativo = False
        db.commit()
        return True