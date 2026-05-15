// Tipos do domínio Equipe 4 — Demanda.
// Espelham o DBML do microserviço SDI.Micro.Demanda.

export type DemandaStatus = "aberta" | "em_negociacao" | "atendida" | "cancelada";
export type RecorrenciaFrequencia = "diaria" | "semanal" | "mensal";

export interface EnderecoEntrega {
  id: string;
  id_empresa: string;
  apelido: string;          // ex.: "Matriz", "Filial SP"
  logradouro: string;
  numero: string;
  complemento?: string;
  bairro: string;
  cidade: string;
  uf: string;
  cep: string;
  ativo: boolean;
  data_criacao: string;
}

export interface DemandaRecorrencia {
  frequencia: RecorrenciaFrequencia;
  quantidade_por_periodo?: number;
  data_inicio: string;      // ISO date
  data_fim?: string;        // ISO date
  dia_preferencial: number | string; // 1..31 (mensal) ou 1..7 (semanal) ou 1 (diária)
}

export interface Demanda {
  id: string;
  id_usuario_criador: string;
  id_empresa_comprador: string;
  id_produto: string;       // projeção local — pode não estar sincronizada
  id_endereco_entrega: string;
  quantidade_desejada: number;
  preco_maximo?: number;
  prioridade: "baixa" | "media" | "alta";
  observacao?: string;
  status: DemandaStatus;
  is_recorrente: boolean;
  recorrencia?: DemandaRecorrencia;
  data_criacao: string;
  atualizado_em: string;
}

export interface WishlistItem {
  id: string;
  id_usuario: string;
  id_empresa: string;
  id_produto: string;
  quantidade_desejada: number;
  observacao?: string;
  convertida_em_demanda: boolean;
  convertido_em_demanda?: boolean;
  id_demanda_gerada?: string;
  data_criacao: string;
}

// Projeção local de Produto (Equipe 2) — alimentada por eventos Kafka.
export interface ProdutoProjecao {
  id: string;
  codigo: string;
  nome: string;
  categoria: string;
  unidade: string;          // sigla
  sincronizado_em: string;
}
