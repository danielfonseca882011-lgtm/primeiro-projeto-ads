
import streamlit as st
from supabase import create_client
from datetime import date
import pandas as pd

# CONFIGURACAO
st.set_page_config(
    page_title="Controle Financeiro",
    page_icon="💰",
    layout="wide"
)

# CONEXAO COM SUPABASE
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# SESSAO DO USUARIO
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None


def autenticar():
    if st.session_state.access_token:
        supabase.auth.set_session(
            st.session_state.access_token,
            st.session_state.refresh_token
        )

        sessao = supabase.auth.get_session()

        if sessao:
            st.session_state.access_token = sessao.access_token
            st.session_state.refresh_token = sessao.refresh_token
            st.session_state.usuario = sessao.user

    return st.session_state.usuario


# TELA DE LOGIN E CADASTRO
if not autenticar():

    st.title("💰 Controle Financeiro")
    st.write("Organize seu dinheiro de forma simples e segura.")

    aba1, aba2 = st.tabs(["Entrar", "Criar conta"])

    with aba1:
        st.subheader("Acessar minha conta")

        with st.form("login"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")

            entrar = st.form_submit_button("Entrar")

            if entrar:
                try:
                    resposta = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": senha
                    })

                    st.session_state.usuario = resposta.user
                    st.session_state.access_token = resposta.session.access_token
                    st.session_state.refresh_token = resposta.session.refresh_token

                    st.rerun()

                except Exception:
                    st.error("E-mail ou senha incorretos, ou conta ainda nao confirmada.")

    with aba2:
        st.subheader("Criar minha conta")

        with st.form("cadastro"):
            nome = st.text_input("Seu nome")
            novo_email = st.text_input("Seu e-mail")
            nova_senha = st.text_input(
                "Crie uma senha",
                type="password"
            )

            cadastrar = st.form_submit_button("Criar conta")

            if cadastrar:
                if not nome.strip() or not novo_email.strip():
                    st.warning("Preencha todos os campos.")

                elif len(nova_senha) < 8:
                    st.warning("A senha precisa ter pelo menos 8 caracteres.")

                else:
                    try:
                        resposta = supabase.auth.sign_up({
                            "email": novo_email,
                            "password": nova_senha,
                            "options": {
                                "data": {
                                    "nome": nome
                                }
                            }
                        })

                        st.success(
                            "Cadastro solicitado! Confira seu e-mail para confirmar sua conta."
                        )

                    except Exception as erro:
                        st.error(f"Erro ao cadastrar: {erro}")

    st.stop()


# PAINEL DO USUARIO
usuario = st.session_state.usuario
user_id = usuario.id

nome_usuario = usuario.user_metadata.get("nome", "Usuario")

st.sidebar.title("💰 Controle Financeiro")
st.sidebar.write(f"Ola, {nome_usuario}!")
st.sidebar.write(usuario.email)

if st.sidebar.button("Sair da conta"):
    supabase.auth.sign_out()

    st.session_state.usuario = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None

    st.rerun()


st.title("📊 Meu Controle Financeiro")
st.write("Acompanhe suas receitas, despesas e saldo.")

# BUSCAR MOVIMENTACOES DO USUARIO
try:
    resposta = (
        supabase.table("movimentacoes")
        .select("*")
        .eq("user_id", user_id)
        .order("data", desc=True)
        .execute()
    )

    movimentacoes = resposta.data

except Exception as erro:
    st.error(f"Erro ao carregar movimentacoes: {erro}")
    st.stop()


# CALCULAR VALORES
total_receitas = sum(
    float(item["valor"])
    for item in movimentacoes
    if item["tipo"] == "Receita"
)

total_despesas = sum(
    float(item["valor"])
    for item in movimentacoes
    if item["tipo"] == "Despesa"
)

saldo = total_receitas - total_despesas


# RESUMO FINANCEIRO
col1, col2, col3 = st.columns(3)

col1.metric(
    "💵 Receitas",
    f"R$ {total_receitas:,.2f}"
)

col2.metric(
    "💸 Despesas",
    f"R$ {total_despesas:,.2f}"
)

col3.metric(
    "💰 Saldo",
    f"R$ {saldo:,.2f}"
)


# GRAFICO DE RECEITAS E DESPESAS
st.subheader("📊 Receitas x Despesas")

dados_grafico = pd.DataFrame({
    "Categoria": ["Receitas", "Despesas"],
    "Valor (R$)": [total_receitas, total_despesas]
})

st.bar_chart(
    dados_grafico,
    x="Categoria",
    y="Valor (R$)",
    use_container_width=True
)

st.divider()st.divider()


# ADICIONAR MOVIMENTACAO
st.subheader("➕ Adicionar movimentacao")

with st.form("nova_movimentacao", clear_on_submit=True):

    tipo = st.selectbox(
        "Tipo de movimentacao",
        ["Receita", "Despesa"]
    )

    descricao = st.text_input("Descricao")

    valor = st.number_input(
        "Valor (R$)",
        min_value=0.01,
        step=1.0
    )

    data_movimentacao = st.date_input(
        "Data",
        value=date.today()
    )

    adicionar = st.form_submit_button("Salvar movimentacao")

    if adicionar:

        if not descricao.strip():
            st.warning("Digite uma descricao.")

        else:
            try:
                supabase.table("movimentacoes").insert({
                    "user_id": user_id,
                    "tipo": tipo,
                    "descricao": descricao,
                    "valor": valor,
                    "data": str(data_movimentacao)
                }).execute()

                st.success("Movimentacao salva com sucesso!")
                st.rerun()

            except Exception as erro:
                st.error(f"Erro ao salvar: {erro}")


# HISTORICO
st.divider()

st.subheader("📋 Historico de movimentacoes")

if movimentacoes:

    df = pd.DataFrame(movimentacoes)

    st.dataframe(
        df[
            ["data", "tipo", "descricao", "valor"]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

  
    st.subheader("✏️ Editar movimentacao")

    opcoes_edicao = {
        f'{item["id"]} - {item["descricao"]} - R$ {item["valor"]}': item
        for item in movimentacoes
    }

    selecionado_edicao = st.selectbox(
        "Escolha a movimentacao para editar",
        list(opcoes_edicao.keys())
    )

    item_edicao = opcoes_edicao[selecionado_edicao]

    with st.form("editar_movimentacao"):
        tipo_editado = st.selectbox(
            "Tipo",
            ["Receita", "Despesa"],
            index=["Receita", "Despesa"].index(item_edicao["tipo"])
        )

        descricao_editada = st.text_input(
            "Descricao",
            value=item_edicao["descricao"]
        )

        valor_editado = st.number_input(
            "Valor (R$)",
            min_value=0.01,
            value=float(item_edicao["valor"]),
            step=1.0
        )

        data_editada = st.date_input(
            "Data da movimentacao",
            value=date.fromisoformat(item_edicao["data"])
        )

        salvar_edicao = st.form_submit_button("Salvar alteracoes")

        if salvar_edicao:
            if not descricao_editada.strip():
                st.warning("Digite uma descricao.")
            else:
                try:
                    (
                        supabase.table("movimentacoes")
                        .update({
                            "tipo": tipo_editado,
                            "descricao": descricao_editada.strip(),
                            "valor": valor_editado,
                            "data": str(data_editada)
                        })
                        .eq("id", item_edicao["id"])
                        .eq("user_id", user_id)
                        .execute()
                    )

                    st.success("Movimentacao atualizada!")
                    st.rerun()

                except Exception as erro:
                    st.error(f"Erro ao editar: {erro}")

    st.divider()
  
    st.subheader("🗑️ Excluir movimentacao")

    opcoes = {
        f'{item["id"]} - {item["descricao"]} - R$ {item["valor"]}': item["id"]
        for item in movimentacoes
    }

    selecionado = st.selectbox(
        "Selecione a movimentacao",
        list(opcoes.keys())
    )

    if st.button("Excluir selecionada"):

        try:
            (
                supabase.table("movimentacoes")
                .delete()
                .eq("id", opcoes[selecionado])
                .eq("user_id", user_id)
                .execute()
            )

            st.success("Movimentacao excluida!")
            st.rerun()

        except Exception as erro:
            st.error(f"Erro ao excluir: {erro}")

else:
    st.info("Voce ainda nao possui movimentacoes cadastradas.")


st.divider()

st.caption("Desenvolvido por Daniel Fonseca | ADS")
