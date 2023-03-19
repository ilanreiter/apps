import streamlit as st
from streamlit_sortables import sort_items
import pandas as pd
import plotly.express as px
import numpy as np
from PIL import Image


# ---------------- TODOs -------------------------------------
#TODO - publish
#TODO - export as XSL and PDF

#------------------------- Congiguration -----------------------
CHART_HIGHT = 500

st.set_option('deprecation.showfileUploaderEncoding', False)
st.set_page_config(
    page_title="Pivot Master",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

#-------------------------------------------------------------
def add_annotation(x, y, val, max_val, fig):
    if pd.notna(val):
        if val > max_val / 2:
            font_color = 'white'
        else:
            font_color = 'black'
        fig.add_annotation(
            x=x, y=y,
            text=str(val),
            showarrow=False,
            font=dict(color=font_color),
        )
    return fig
#----------------------------------------------------------------
def format_labels(label):
    if data[label].dtype in [float, int]:
        icon = "~🔢"
    elif data[label].dtype == "object":
        icon = "~🔠"
    elif data[label].dtype == 'datetime64[ns]':
        icon = "~📅"
    else:
        icon = "~❓"
    return(label+ icon)
#----------------------------------------------------------------
def concat_columns(df, cols):
  # convert non-string columns to string
  df[cols] = df[cols].astype(str)
  concat_name = '+'.join(cols)
  # create a new column by joining all columns in the list
  df[concat_name] = pd.Series(map('+'.join, df[cols].values.tolist()), index=df.index)
  # return the dataframe with the new column
  return df[concat_name].name
#----------------------------------------------------------------
@st.cache_data
def summary_table(data):
        # Show Summary Table
    #---------------------
    st.write("### Summary Table")

    summary_table = pd.concat([data.dtypes, data.describe().T], axis=1)
    summary_table.reset_index(inplace=True)
    summary_table = summary_table.rename(columns={0: 'Type'})
    summary_table = summary_table.rename(columns={'index': 'Column Name'})
    summary_table['Column Name'] = summary_table['Column Name'].apply(format_labels)
    summary_table = summary_table.applymap(lambda x: round(x, 1) if isinstance(x, (int, float)) else x)
    st.dataframe(summary_table.style.format({'count': '{:.0f}'}))
    st.markdown("""---""")
    return(summary_table)

# -------- round floats -----------------------------------------
def round_floats(data):
    for col in data.columns:
        if data[col].dtype == float:
            data[col] = data[col].round(1)
    return(data)

#---------- pivot_table --------------------------------------------------
def pivot_table(data, h_cols, v_cols, val_cols, agg_func):
#Create the pivot table based on the user's selections

    pivot_table = pd.pivot_table(data, values=val_cols, index=v_cols, columns=h_cols, aggfunc=agg_func)
    # if the first level of columns is None, drop it
    if isinstance(pivot_table.columns, pd.MultiIndex) and pivot_table.columns.names[0] is None and len(val_cols) == 1:
        pivot_table.columns = pivot_table.columns.droplevel()
    pivot_table = round_floats(pivot_table)
    # Display the pivot table
    st.subheader(f"Pivot Table of columns: :blue[{h_cols}] and rows: :blue[{v_cols}] by values: :blue[{val_cols}]")

    #Transpose table?
    transpose = st.checkbox('Transpose Pivot Table?')
    if transpose:
        pivot_table = pivot_table.T
        h_cols, v_cols = v_cols, h_cols

    #Styling the table
    pivot_table.style.highlight_null().background_gradient(cmap='coolwarm')

    st.dataframe(pivot_table)
    st.markdown("---")

    # Create the pivot chart based on the user's selections
    def tup2str(x):
        s = str(x)
        for char in "()[]'":
            s = s.replace(char,"")
        s = s.replace(",","+")
        return(s)
    
    #Create heatmap chart with the pivot data
    x = list(map(tup2str, pivot_table.columns))
    y = list(map(tup2str, pivot_table.index))
    # st.write(f"x: {x}, y: {y}")


    fig1 = px.imshow(pivot_table, x=x, y=y, labels= dict(x=tup2str(h_cols), y=tup2str(v_cols), color = tup2str(val_cols)),
                    color_continuous_scale='viridis', text_auto=True,  height=CHART_HIGHT)

    # Add the actual values to the heatmap chart
    fig1.update_layout(xaxis=dict(side='top'))
    fig1.update_traces(hoverongaps=False)
    # Display the pivot chart
    st.subheader(f"Pivot Chart of columns: :blue[{h_cols}] and rows: :blue[{v_cols}] by values: :blue[{val_cols}]")
    st.plotly_chart(fig1,   use_container_width=True,)
    st.markdown("---")
#----------------------------------------------------------------------------------
def bar_chart(data, x, y, color = None, agg_func = sum):

    _x, _y = x, y
    if x:
        x = concat_columns(data, x)          
    if color:
        color = concat_columns(data, color)

    st.write(f"x: {x}, color: {color}")

    group_by = [e for e in [x, color] if e]
    pivot_table = data.groupby(group_by)[y].aggregate(agg_func).reset_index()
    pivot_table = round_floats(pivot_table)

    x = color if not x else x
    color = x if not color else color

    #In case there is more then one y metric: melt the dataframe
    if len(y)>1:
        pivot_table = pd.melt(pivot_table, id_vars = group_by, value_vars=y)
        y = 'value'
        facets = 'variable'
    else:
        y = y[0]
        facets = None
    
    # st.subheader("Pivot Bar Chart")
    st.subheader(f"Treemap Bar Chart of values: :blue[{color}] by: :blue[{_x}]")
    #Transpose table?
    c1,c2 = st.columns((2,8)) 
    transpose = c1.checkbox('Transpose Pivot Table?', key=2 )
    stacked = c2.checkbox('Stacked Bars?', key=3 )
    if transpose:
        x, color = color, x
    stacked = 'stack' if stacked else 'group'

    #Create the chart
    fig = px.bar(pivot_table, x = x, y = y, color = color, facet_row=facets, text=y, height=CHART_HIGHT, barmode = stacked )
    fig.update_xaxes(categoryorder='category ascending')
    st.plotly_chart(fig, use_container_width=True,)
    st.markdown("---")
#--------------------------------------------------------------------
def tree_map(data, x, y, z):
    ct = st.container()
    # ct.subheader("Treemap Chart")
    # ct.write(f"x: {x}, y: {y}")
    # ct.dataframe(data)
    # ct.markdown("---")
    if len(x) > 0 and len(z) > 0:
        ct.subheader(f"Treemap of rows: :blue[{x}] and value: :blue[{z[0]}]")
        fig = px.treemap(data, path=x, values=z[0], color = concat_columns(data, x) ,  height=500)
        fig.data[0].textinfo = 'label+text+value+percent root'
        ct.plotly_chart(fig, use_container_width=True,)
        ct.markdown("---")
    if len(y) > 0 and len(z) > 0:
        ct.subheader(f"Treemap of columns: :blue[{y}] and value: :blue[{z[0]}]")
        fig = px.treemap(data, path=y, values=z[0],  color = concat_columns(data, y), height=500, hover_data = y)
        fig.data[0].textinfo = 'label+text+value+percent parent'
        ct.plotly_chart(fig, use_container_width=True,)  
        ct.markdown("---")

#-----------------------------------------------------------------
#                          Main
#-----------------------------------------------------------------

# Set the title of the app
c1, c2 , c3 = st.columns((2, 6, 2))
c2.markdown("<h1 style='text-align: center;'> Pivot Master </h1>", unsafe_allow_html=True)
c1.image('https://cdn.icon-icons.com/icons2/2596/PNG/512/pivot_table_icon_154985.png', width=100)
txt = c3.markdown(f"#### :arrow_right_hook: App Description")
txt = c3.markdown(f"Pivot Master is an app that allows you to create pivot tables and charts from your data.\
                   You can input a csv file and see a list of columns in the sidebar. You can drag and drop the columns to select the pivot rows, columns and values. \
                   The app will automatically generate pivot tables and charts accordingly. You can customize the format, style and layout of your tables and charts.\
                   You can also export your results as pdf, excel or image files. Pivot Master is a powerful and easy-to-use tool for data analysis and visualization. \
                   ")
st.markdown('---')
# Allow the user to upload a CSV file
uploaded_file = st.file_uploader('Upload a CSV file', type='csv')
st.markdown('---')

# Check if the user has uploaded a file
if uploaded_file is not None:

    # Load the data into a Pandas DataFrame
    data = pd.read_csv(uploaded_file)

#Preapar bins for the drag and drop bins
    all_items = [
        {'header': 'Available Elements 🆕',  'items': [format_labels(col) for col in data.columns]},
        {'header': 'Rows ➡️', 'items':[]},
        {'header': 'Columns ⬇', 'items':[]},
        {'header': 'Values 🔢', 'items':[]},
    ]

    with st.sidebar:
        st.header("Drag and Drop Pivot Elements")
        st.markdown("<mark style='background-color: green;'>Drag and Drop Pivot Elements</mark>",  unsafe_allow_html=True)
        sorted_items = sort_items(all_items, multi_containers=True,  direction='vertical')
        st.markdown("---")
        aggregation_method = st.selectbox('Select Aggregation Method', ['sum', 'mean', 'median'])
        st.sidebar.markdown("---")

    #convert the bins to lists of column names and removing the icons
    pivot_elements = {}
    for item in sorted_items:
        pivot_elements[item['header'].split(' ', 1)[0]] =  [e.split('~',1)[0] for e in item['items']]
    #Plot the pivot charts
    if (pivot_elements['Columns'] or pivot_elements['Rows']) and pivot_elements['Values']:
        pivot_table(data,  pivot_elements['Columns'] , pivot_elements['Rows'], pivot_elements['Values'], aggregation_method)
        bar_chart(data, x = pivot_elements['Columns'] , y = pivot_elements['Values'],  color =  pivot_elements['Rows'],agg_func=aggregation_method)
        tree_map(data, x = pivot_elements['Rows'] , y = pivot_elements['Columns'], z = pivot_elements['Values'])
   
else:
    st.write("Select columns for pivot table and chart")