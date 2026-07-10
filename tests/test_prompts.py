import pytest

from src.services.prompts import construir_prompt, parse_resposta_ia


def test_construir_prompt_inclui_itens_e_historico():
    itens = [{"descricao": "UBER 123", "valor": "20", "tipo_valor": "saida"}]
    historico = [("PADARIA DOCE", "ALIMENTACAO", "Refeições")]
    prompt = construir_prompt(itens, historico)
    assert "UBER 123" in prompt
    assert "PADARIA DOCE -> ALIMENTACAO / Refeições" in prompt
    assert "RECEITAS:" in prompt  # taxonomia de receitas incluída


def test_parse_resposta_ia_alinha_itens():
    itens = [
        {"descricao": "UBER", "tipo_valor": "saida"},
        {"descricao": "SALARIO", "tipo_valor": "entrada"},
    ]
    texto = (
        '```json\n[{"descricao":"UBER","categoria":"TRANSPORTE",'
        '"subcategoria":"Uber Taxi Metro","confianca":"alta"},'
        '{"descricao":"SALARIO","categoria":"SALARIO FRED",'
        '"subcategoria":"","confianca":"alta"}]\n```'
    )
    resultados = parse_resposta_ia(texto, itens)
    assert resultados[0]["categoria"] == "TRANSPORTE"
    assert resultados[0]["origem"] == "ia"
    assert resultados[1]["tipo_valor"] == "entrada"


def test_parse_resposta_ia_contagem_divergente_falha():
    itens = [{"descricao": "A", "tipo_valor": "saida"}]
    with pytest.raises(ValueError):
        parse_resposta_ia("[]", itens)
