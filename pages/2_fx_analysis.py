import json
import streamlit as st
import plotly.graph_objects as go
from src.fx_corr import corr_data



options = st.multiselect(
    'select currencies',
    json.load(open('./src/curcodes.json')),
    ['GBP', 'EUR'])

if options == [] or len(options) < 2:
    st.write('Please choose at least 2 currencies')
else:
    pairs = []
    for i in range(len(options)-1):
        for j in range(i+1, len(options)):
            pairs.append(options[i]+options[j])
    currs, corrs = corr_data(pairs)

    fig1 = go.Figure()
    for cur in options:
        fig1.add_trace(go.Scatter(x=currs.index, y=currs[cur].values, mode="lines",name=cur))
    fig1.update_layout(title='currencies relative to USD')
    st.plotly_chart(fig1, use_container_width=True)

    fig1 = go.Figure()
    for corr in pairs:
        fig1.add_trace(go.Scatter(x=corrs.dropna().index, y=corrs.dropna()[corr].values, mode="lines",name=corr))
    fig1.update_layout(title='correlations')
    st.plotly_chart(fig1, use_container_width=True)


