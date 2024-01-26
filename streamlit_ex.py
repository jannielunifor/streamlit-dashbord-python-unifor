import re
import base64

import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

#
df_ibyte = pd.read_csv('RECLAMEAQUI_IBYTE.csv')
df_hapvida = pd.read_csv('RECLAMEAQUI_HAPVIDA.csv')
df_nagem = pd.read_csv('RECLAMEAQUI_NAGEM.csv')

df_ibyte['EMPRESA'] = 'IBYTE'
df_hapvida['EMPRESA'] = 'HAPVIDA'
df_nagem['EMPRESA'] = 'NAGEM'

df = pd.concat([df_ibyte, df_hapvida, df_nagem])

#
def get_local(x, pos):
    y = (re.sub(r'^([\w \d-]+) \- (\S+)$', pos, x, 1)).upper().strip()
    if y == 'C':
        return 'CE'
    if y == 'P':
        return 'PI'
    if y == 'NAOCONSTA' or y == '--':
        return '-'
    return y

df['TEMPO']=pd.to_datetime(df['TEMPO'])
df['STATUS'] = df['STATUS'].astype("category")
df['CIDADE'] = df['LOCAL'].apply(lambda x: get_local(x, r'\1'))
df['ESTADO'] = df['LOCAL'].apply(lambda x: get_local(x, r'\2'))
df['TAMANHO_TEXTO'] = df['DESCRICAO'].apply(lambda x: len(x))

#
df['CATEGORIA'].apply(lambda x: x.split('<->'))

itens = {}
for row in df['CATEGORIA'].apply(lambda x: x.split('<->')):
    for x in row:
        itens[x] = itens[x] = itens[x] + 1 if x in itens.keys() else 1

df_categorias = pd.DataFrame(itens.items(), columns=['Categoria', 'Ocorrencias'])
df_categorias.sort_values(by = 'Ocorrencias', ascending=False).head(5)

#
lista_empresas = list(df['EMPRESA'].unique())
lista_estados = list(df.sort_values(by = 'ESTADO')['ESTADO'].unique())

side = st.sidebar

side.write('Filtros')
empresa = side.selectbox('Selecione a Empresa', lista_empresas)

df_f = df[df['EMPRESA'] == empresa]
lista_anos = list(df_f['ANO'].unique())

ano = side.selectbox('Selecione o ano', ['TODOS'] + lista_anos)
estado = side.selectbox('Selecione o Estado', ['TODOS'] + lista_estados)

max = df_f['TAMANHO_TEXTO'].max()
start, end = side.select_slider('Tamanho do texto', options=range(0, max + 1), value=(0, max))



df_ano = df_f
df_ano = df_ano[df_ano['ANO'] == ano] if ano != 'TODOS' else df_ano
df_ano = df_ano[df_ano['ESTADO'] == estado] if estado != 'TODOS' else df_ano
df_ano = df_ano[(df_ano['TAMANHO_TEXTO'] <= end) & (df_ano['TAMANHO_TEXTO'] >= start)]

side_bg = base64.b64encode(open('reclame-aqui-logo.png', "rb").read()).decode()
st.markdown(
    f"<style>.main{{background:url(data:image/png;base64,{side_bg}) no-repeat top 3rem center;background-size:10rem;}}</style>",
    unsafe_allow_html=True
)

st.title('Análise de Dados do Reclame Aqui')
st.caption('Trabalho para Dashboards em Python - Prof. Jorge Araujo')
col1, col2, col3, col4 = st.columns(4)
col1.write(f"Empresa: {empresa}")
col2.write(f"Estado: {estado}")
col3.write(f"Ano: {ano}")
texto = f"{start} à {end} letras" if end < max or start > 0 else 'Texto: TODOS'
col4.write(texto)

casos = df_ano['CASOS'].count()
resolvidos = df_ano[df_f['STATUS'] == 'Resolvido']['CASOS'].count()
n_respondidas = df_ano[df_f['STATUS'] == 'Não respondida']['CASOS'].count()

col1, col2, col3, col4 = st.columns(4)

col1.metric(label = 'Reclamações', value = casos)
col3.metric(label = 'Não Respondidas', value = '{:.1f}%'.format(n_respondidas / casos * 100))
col4.metric(label = 'Resolvido', value = '{:.1f}%'.format(resolvidos / casos * 100))

tab1, tab2, tab3, tab4 = st.tabs(["Período", "Estados", "Situação", "Dados"])

with tab1:
    # st.write('Reclamações por Período')
    # ax = df_ano.sort_values(by = ['ANO', 'MES']).groupby(["MES","ANO"])["CASOS"].count().plot(style="-o", figsize= (15,5))
    # ax.set_xlabel("Mês, Ano")
    # ax.set_ylabel("Reclamações")
    # st.pyplot(ax.figure)
    df_p = df_ano.sort_values(by = 'TEMPO').groupby("TEMPO")["CASOS"].count().reset_index()
    df_p = df_p.groupby(df_p['TEMPO'].dt.strftime('%Y-%m'))['CASOS'].count().reset_index()
    df_p = df_p.rename(columns={'CASOS': 'Reclamações', 'TEMPO': 'Mes Ano'})
    figp = px.line(df_p, x='Mes Ano', y='Reclamações', title = 'Reclamações por Período')
    st.plotly_chart(figp)

with tab2:
    # st.write('Reclamações por Estado')
    # ax = df_ano.sort_values(by = 'ESTADO').groupby("ESTADO")["CASOS"].count().plot(kind="bar", figsize=(15,5))
    # ax.set_xlabel("Estado")
    # ax.set_ylabel("Reclamações")
    # st.pyplot(ax.figure)
    df_p = df_ano.sort_values(by = 'ESTADO').groupby("ESTADO")["CASOS"].count().reset_index()
    df_p = df_p.rename(columns={'CASOS': 'Reclamações', 'ESTADO': 'Estado'})
    figp = px.bar(df_p, x='Estado', y='Reclamações', title = 'Reclamações por Estado')
    st.plotly_chart(figp)

with tab3:
    df_p = df_ano.sort_values(by = 'STATUS').groupby("STATUS")["CASOS"].count().reset_index()
    df_p = df_p.rename(columns={'CASOS': 'Reclamações', 'STATUS': 'Situação'})
    figp = px.bar(df_p, x='Situação', y='Reclamações', title = 'Reclamações por Situação')
    st.plotly_chart(figp)

with tab4:
    df_show = df_ano.drop(columns=[
        'LOCAL', 'ANO', 'MES', 'DIA', 'DIA_DO_ANO', 'SEMANA_DO_ANO',
        'DIA_DA_SEMANA', 'TRIMETRES', 'EMPRESA', 'CASOS'
    ])
    st.dataframe(df_show)