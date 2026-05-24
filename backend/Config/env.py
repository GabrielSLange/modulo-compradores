import os
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def load_env() -> None:
    caminhos = [
        Path(__file__).resolve().parents[2] / ".env",
        Path(__file__).resolve().parents[1] / ".env",
    ]

    for caminho in caminhos:
        if not caminho.exists():
            continue

        for linha in caminho.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue

            chave, valor = linha.split("=", 1)
            os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))
        return


def get_env(nome: str, default: str | None = None, *, required: bool = False) -> str | None:
    load_env()
    valor = os.getenv(nome, default)
    if required and not valor:
        raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {nome}")
    return valor


def get_env_int(nome: str, default: int | None = None, *, required: bool = False) -> int:
    valor = get_env(nome, required=required)
    if valor is None or valor == "":
        if default is None:
            raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {nome}")
        return default
    return int(valor)


def get_env_bool(nome: str, default: bool | None = None, *, required: bool = False) -> bool:
    valor = get_env(nome, required=required)
    if valor is None or valor == "":
        if default is None:
            raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {nome}")
        return default
    return valor.lower() in {"1", "true", "yes", "sim", "on"}


def get_env_list(nome: str, default: list[str] | None = None, *, required: bool = False) -> list[str]:
    valor = get_env(nome, required=required)
    if not valor:
        if default is None:
            raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {nome}")
        return default
    return [item.strip() for item in valor.split(",") if item.strip()]
