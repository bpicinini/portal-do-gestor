# Portal do Gestor

Aplicação privada em Streamlit para gestão de equipe, organograma, movimentações, manpower e performance.

## Rodar localmente

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Deploy

O projeto está preparado para deploy em Streamlit Community Cloud ou outro host compatível com Streamlit.

1. Publique o projeto em um repositório Git.
2. Configure as dependências com `requirements.txt`.
3. Adicione os segredos de produção usando o modelo de `.streamlit/secrets.example.toml`.
4. Defina `app.py` como entrypoint da aplicação.

## Observação sobre dados

Sem segredos configurados, o app usa o arquivo local `data/dados.xlsx`. Em produção, com `GITHUB_TOKEN` e `GITHUB_REPO`, ele passa a ler e salvar a planilha no GitHub.
