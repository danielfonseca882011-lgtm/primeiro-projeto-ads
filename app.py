import streamlit as st

st.set_page_config(page_title="Controle Financeiro", page_icon="💰", layout="wide")

if "receitas" not in st.session_state:
    st.session_state.receitas = []

if "despesas" not in st.session_state:
    st.session_state.despesas = []

st.title("💰 Controle Financeiro")
st.write("Projeto desenvolvido por Daniel Fonseca - ADS")

st.divider()

total_receitas = sum(st.session_state.receitas)
total_despesas = sum(st.session_state.despesas)
saldo = total_receitas - total_despesas

col1, col2, col3 = st.columns(3)

col1.metric("💵 Receitas", f"R$ {total_receitas:.2f}")
col2.metric("💸 Despesas", f"R$ {total_despesas:.2f}")
col3.metric("💰 Saldo", f"R$ {saldo:.2f}")

st.divider()

st.subheader("Adicionar movimentação")

tipo = st.selectbox("Tipo de movimentação", ["Receita", "Despesa"])
valor = st.number_input("Valor (R$)", min_value=0.01, step=10.0)

if st.button("Adicionar"):
    if tipo == "Receita":
        st.session_state.receitas.append(valor)
        st.success("Receita adicionada com sucesso!")
    else:
        st.session_state.despesas.append(valor)
        st.success("Despesa adicionada com sucesso!")
    st.rerun()

st.divider()

st.subheader("📊 Resumo financeiro")

st.bar_chart({
    "Receitas": [total_receitas],
    "Despesas": [total_despesas]
})

st.caption("Meu primeiro projeto web em Python | Daniel Fonseca")