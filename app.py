
import streamlit as st
from supabase import create_client
from datetime import date
import pandas as pd
from io import BytesIO
from openpyxl.styles import Font, PatternFill

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

# FILTRO POR MES E ANO
st.subheader("📅 Filtrar por período")

meses = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março",
    4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro",
    10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

col_mes, col_ano = st.columns(2)

with col_mes:
    mes_selecionado = st.selectbox(
        "Mês",
        list(meses.keys()),
        index=date.today().month - 1,
        format_func=lambda mes: meses[mes]
    )

with col_ano:
    ano_selecionado = st.number_input(
        "Ano",
        min_value=2000,
        max_value=2100,
        value=date.today().year,
        step=1
    )

movimentacoes = [
    item for item in movimentacoes
    if date.fromisoformat(item["data"]).month == mes_selecionado
    and date.fromisoformat(item["data"]).year == ano_selecionado
]
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
    "Receitas": [total_receitas, 0],
    "Despesas": [0, total_despesas]
})

st.bar_chart(
    dados_grafico,
    x="Categoria",
    y=["Receitas", "Despesas"],
    color=["#16A34A", "#DC2626"],
    stack=False,
    use_container_width=True
)

st.divider()


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

# RELATORIO MENSAL EM EXCEL
st.divider()
st.subheader("📥 Relatório mensal em Excel")

def gerar_relatorio_excel():
    arquivo = BytesIO()

    linhas = [
        {
            "Data": item["data"],
            "Tipo": item["tipo"],
            "Descrição": item["descricao"],
            "Valor (R$)": float(item["valor"])
        }
        for item in movimentacoes
    ]

    df_relatorio = pd.DataFrame(
        linhas,
        columns=["Data", "Tipo", "Descrição", "Valor (R$)"]
    )

    with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
        df_relatorio.to_excel(
            writer,
            sheet_name="Movimentações",
            index=False
        )

        resumo = pd.DataFrame({
            "Indicador": ["Receitas", "Despesas", "Saldo"],
            "Valor (R$)": [
                total_receitas,
                total_despesas,
                saldo
            ]
        })

        resumo.to_excel(
            writer,
            sheet_name="Resumo",
            index=False
        )

        for planilha in writer.book.worksheets:
            planilha.freeze_panes = "A2"

            for celula in planilha[1]:
                celula.font = Font(color="FFFFFF", bold=True)
                celula.fill = PatternFill(
                    fill_type="solid",
                    fgColor="1F4E78"
                )

            for coluna in planilha.columns:
                letra = coluna[0].column_letter
                maior = max(
                    len(str(celula.value or ""))
                    for celula in coluna
                )
                planilha.column_dimensions[letra].width = min(
                    maior + 3, 35
                )

    arquivo.seek(0)
    return arquivo.getvalue()


st.download_button(
    label="📥 Baixar relatório em Excel",
    data=gerar_relatorio_excel(),
    file_name=f"relatorio_{ano_selecionado}_{mes_selecionado:02d}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
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
