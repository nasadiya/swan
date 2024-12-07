import re, io, zipfile
import pandas as pd
import datetime as dt
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta

reg_pattern = r'[0-3][0-9].[0-1][0-9].20[0-2][0-9]'
ms_form = "%d.%m.%Y %H:%M:%S.%f"
time = 'Gmt time'
time_bin = 'time_bin'
time_periods = ["30s", "10s", "5s", "1s", "100ms", "10ms"]
time_period_values = [30, 10, 5, 1, 0.1, 0.01]

def create_zip(df_list):
    buffer = io.BytesIO()  # In-memory buffer for the ZIP file
    with zipfile.ZipFile(buffer, "w") as zf:
        for index, df in enumerate(df_list):
            csv = io.StringIO()
            df.to_csv(csv, index=False)
            zf.writestr("data"+str(index+1)+".csv", csv.getvalue())
    
    buffer.seek(0)  # Move to the start of the buffer
    return buffer

# App title
st.title("Tick Analysis")

# File uploader for multiple CSV files
uploaded_files = st.file_uploader("Drag and drop CSV files here", type="csv", accept_multiple_files=True)

if uploaded_files:
    file_holder = []
    file_dates = []
    for file in uploaded_files:
        date = re.findall(pattern=reg_pattern,string=file.name)[0]
        df = pd.read_csv(file)
        df[time] = df[time].apply(lambda x :dt.datetime.strptime(x,ms_form))
        file_holder.append(df)
        file_dates.append(date)
        
    with st.sidebar:
        event_time = st.time_input("Enter event time (24hr)",
                                    value = None,
                                    step=60)
        

        lookback = st.number_input("Enter look back in seconds",
                                    value=5, max_value=60, min_value=1,step=1)

        lookahead = st.number_input("Enter look ahead in seconds",
                                    value=5,max_value=60, min_value=1,step=1)

        timeperiod = st.selectbox("timeperiod :",
                                    options=time_periods,
                                    index=4)

        variable = st.selectbox("variable :",
                                    options=['Bid','Ask','BidVolume','AskVolume'],
                                    index=1)

    if (event_time is not None) & (lookahead is not None) & (lookback is not None):
        file_dates = [dt.datetime.combine(dt.datetime.strptime(file_date, "%d.%m.%Y"), 
                                            event_time) 
                                        for file_date in file_dates]
        file_lookbacks = [file_date - relativedelta(seconds=lookback)
                            for file_date in file_dates]
        file_lookaheads = [file_date + relativedelta(seconds=lookahead) 
                            for file_date in file_dates]
        
        # filter the files for the timperiod required
        if (timeperiod is not None) and (variable is not None):
            filtered_datasets = []
            timeperiod_value = time_period_values[time_periods.index(timeperiod)]
            fig = go.Figure()
            for index, file in enumerate(file_holder):
                event_highlight = [file_dates[index] - relativedelta(seconds=timeperiod_value),
                                   file_dates[index] + relativedelta(seconds=timeperiod_value)]
                filter_range = (file[time]<=file_lookaheads[index]) & (file[time]>=file_lookbacks[index])
                file_filtered = file.loc[filter_range,[time,variable]]
                filtered_datasets.append(file.loc[filter_range,:])
                file_filtered[time_bin] = file_filtered[time].dt.round(timeperiod)
                file_filtered.drop(columns=time,inplace=True)
                # create the full bin to which this must conform to 
                bins = pd.date_range(start=file_lookbacks[index],
                                        end=file_lookaheads[index],
                                        freq=timeperiod)
                df_bin = pd.DataFrame(pd.Index(data=bins,name=time_bin))
                # merge and take care of missings
                file_filtered = pd.merge(df_bin,file_filtered,how='left',on='time_bin').bfill().ffill()
                # change the time_bin from datetime to time
                file_filtered[time_bin] = file_filtered[time_bin].apply(lambda x : x.time())
                # create the required stats
                file_aggregated = (file_filtered.groupby(time_bin))[variable].agg(['first','max','min','last'])
                file_aggregated.reset_index(inplace=True)
                file_aggregated["midpoint"] = (file_aggregated["first"] + file_aggregated["last"]) / 2
                fig.add_trace(
                            go.Candlestick(
                                x=file_aggregated[time_bin],  # Time
                                open=file_aggregated["first"],    # Open values
                                high=file_aggregated["max"],    # High values
                                low=file_aggregated["min"],      # Low values
                                close=file_aggregated["last"],  # Close values
                                )
                                
                                )
                fig.add_trace(
                        go.Scatter(
                            x=file_aggregated[time_bin],
                            y=file_aggregated["midpoint"],
                            mode="lines",
                            name=file_dates[index].strftime("%Y-%m-%d"),
                            line=dict(width=1),
                            )
                            )
                        # Customize Layout
            fig.add_vrect(
                x0=event_highlight[0].time(), x1=event_highlight[1].time(),  # Specify the range on the x-axis
                fillcolor="yellow",                # Highlight color
                opacity=0.3,                       # Transparency
                layer="below",                     # Place the highlight below the chart
                line_width=0,                      # No border
            )
            fig.update_layout(
                title="Event Tick movement",
                xaxis_title="Time",
                yaxis_title=variable,
                xaxis_rangeslider_visible=False,  # Add range slider for zooming (set to True if needed)
                )
            st.plotly_chart(fig)

            
            # Create the ZIP file
            zip_file = create_zip(filtered_datasets)
            # Download button for the ZIP file
            st.write("Download filtered Zip files : (filters - Event time, look ahead & lookback)")
            st.download_button(
                label="Download ",
                data=zip_file,
                file_name="filtered_tick_data.zip",
                mime="application/zip"
            )