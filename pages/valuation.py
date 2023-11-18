import streamlit as st
import pandas as pd
from src.valuation.irswap import make_instruments, calculate_swap


st.title('IRswap Valuation')

st.write('Enter parameters and submit')
with st.form(key='my-form', clear_on_submit=False):
    col0, col1, col2, col3, col4 = st.columns(5)
    with col0:
        r_6m = st.number_input('6m',0.000,1.000, 0.025, step=0.0001, format='%.4f')

    with col1:
        r_1y = st.number_input('1Y',0.000,1.000, 0.031, step=0.0001, format='%.4f')

    with col2:
        r_2y = st.number_input('2Y',0.000,1.000, 0.032, step=0.0001, format='%.4f')

    with col3:
        r_3y = st.number_input('3Y',0.000,1.0000, 0.035, step=0.0001, format='%.4f')

    with col4:
        r_4y = st.number_input('4Y',0.0000,1.0000, 0.040, step=0.0001, format='%.4f')
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        tenor = st.text_input('tenor','3y')

    with col6:
        fixed_rate = st.number_input('fixed_rate', 0.0, 0.1, 0.0)

    with col7:
        forward_start = st.text_input('fwd_start','2D')

    with col8:
        nominal = st.number_input('nominal',0.0,1e15,1e6)

    run = st.form_submit_button('Submit')

if run:
    instruments = make_instruments(r_6m, r_1y, r_2y, r_3y, r_4y)
    swap = calculate_swap(instruments, tenor, fixed_rate, forward_start, nominal)

    st.write(pd.DataFrame(data={
        'Fair Rate':swap.fairRate(),
        'NPV':swap.NPV()
    }))

    leg1 = swap.leg(1)

    #st.line_chart(x=leg1.date(), y=leg1.amount())