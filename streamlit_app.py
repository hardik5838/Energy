#######################
# Import libraries
import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt

#######################
# Page configuration
st.set_page_config(
    page_title="Asepeyo Energy Efficiency Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

alt.themes.enable("blue")

#######################
# Load and process data
@st.cache_data
def load_data(file_path):
    """Loads and processes the energy audit data."""
    try:
        df = pd.read_csv(file_path)
        # Clean column names
        df.columns = df.columns.str.strip()
        # Convert numeric columns, filling errors with 0
        for col in ['Energy Saved', 'Money Saved', 'Investment', 'Pay back period']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df.fillna(0, inplace=True)
        return df
    except FileNotFoundError:
        st.error(f"Error: The file '{file_path}' was not found. Please make sure the file is in the correct directory.")
        return pd.DataFrame() # Return empty DataFrame on error

# Provide the correct path to your CSV file
df = load_data('data/2025 Energy Audit summary - Sheet1 (1).csv')

if not df.empty:

    #######################
    # Sidebar Filters
    with st.sidebar:
        st.title('⚡ Asepeyo Energy Dashboard')
        
        # Filter by Autonomous Community
        community_list = ['All'] + sorted(df['Comunidad Autónoma'].unique().tolist())
        selected_community = st.selectbox('Select a Community', community_list)

        # Filter data based on selection
        if selected_community == 'All':
            df_filtered = df
        else:
            df_filtered = df[df['Comunidad Autónoma'] == selected_community]

    #######################
    # Main Panel
    st.title(f"Energy Efficiency Analysis: {selected_community}")

    # --- Key Performance Indicators (KPIs) ---
    total_investment = df_filtered['Investment'].sum()
    total_money_saved = df_filtered['Money Saved'].sum()
    total_energy_saved = df_filtered['Energy Saved'].sum()
    
    # Avoid division by zero
    if total_investment > 0:
        roi = (total_money_saved / total_investment) * 100
    else:
        roi = 0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(label="Total Investment", value=f"€ {total_investment:,.0f}")
    kpi2.metric(label="Total Money Saved", value=f"€ {total_money_saved:,.0f}")
    kpi3.metric(label="Total Energy Saved", value=f"{total_energy_saved:,.0f} kWh")
    kpi4.metric(label="Return on Investment (ROI)", value=f"{roi:.2f} %")
    
    st.markdown("---")


    # --- Chart Layout ---
    col1, col2 = st.columns(2, gap="large")

    with col1:
        # --- Chart 1: Measures required per community/center ---
        st.subheader("Measure Counts")
        if selected_community == 'All':
            # Chart 1: Measures required per community
            measures_per_community = df.groupby('Comunidad Autónoma')['Measure'].count().reset_index().rename(columns={'Measure': 'Count'})
            fig1 = px.bar(
                measures_per_community.sort_values('Count', ascending=False),
                x='Comunidad Autónoma', y='Count', title='Measures per Community',
                labels={'Count': 'Number of Measures', 'Comunidad Autónoma': 'Community'}
            )
        else:
            # Chart 3 (adapted): Measures per Center in the selected community
            measures_per_center = df_filtered.groupby('Center')['Measure'].count().reset_index().rename(columns={'Measure': 'Count'})
            fig1 = px.bar(
                measures_per_center.sort_values('Count', ascending=False),
                x='Center', y='Count', title=f'Measures per Center in {selected_community}',
                labels={'Count': 'Number of Measures'}
            )
        st.plotly_chart(fig1, use_container_width=True)

        
        # --- Chart 5: Energy Savings per community ---
        st.subheader("Energy Savings Analysis")
        energy_savings_community = df_filtered.groupby('Comunidad Autónoma')['Energy Saved'].sum().reset_index()
        fig5 = px.bar(
            energy_savings_community.sort_values('Energy Saved', ascending=False),
            x='Comunidad Autónoma', y='Energy Saved', title='Energy Savings (kWh) per Community',
            labels={'Energy Saved': 'Total Energy Saved (kWh)', 'Comunidad Autónoma': 'Community'}
        )
        st.plotly_chart(fig5, use_container_width=True)


        # --- Chart 4: Investment Summary Table ---
        st.subheader("Investment Summary by Region")
        regional_investment_summary = df_filtered.groupby('Comunidad Autónoma').agg(
            Total_Investment=('Investment', 'sum'),
            Measure_Count=('Measure', 'count')
        ).reset_index()
        # Avoid division by zero
        regional_investment_summary['Average_Investment_per_Measure'] = regional_investment_summary.apply(
            lambda row: row['Total_Investment'] / row['Measure_Count'] if row['Measure_Count'] > 0 else 0, axis=1
        )
        st.dataframe(
            regional_investment_summary,
            use_container_width=True,
            column_config={
                "Comunidad Autónoma": "Community",
                "Total_Investment": st.column_config.NumberColumn("Total Investment (€)", format="€ %.2f"),
                "Measure_Count": "Number of Measures",
                "Average_Investment_per_Measure": st.column_config.NumberColumn("Avg. Investment/Measure (€)", format="€ %.2f")
            },
            hide_index=True
        )


    with col2:
        # --- Chart 6: Economic Savings ---
        st.subheader("Economic Savings Analysis")
        economic_savings_community = df_filtered.groupby('Comunidad Autónoma')['Money Saved'].sum().reset_index()
        fig6_donut = px.pie(
            economic_savings_community,
            names='Comunidad Autónoma', values='Money Saved',
            title='Contribution to Total Economic Savings',
            hole=0.4
        )
        st.plotly_chart(fig6_donut, use_container_width=True)

        
        # --- Chart 7: Investment vs. Savings Scatter Plot ---
        st.subheader("Investment vs. Financial Savings")
        financial_summary = df_filtered.groupby('Comunidad Autónoma').agg(
            Total_Investment=('Investment', 'sum'),
            Total_Money_Saved=('Money Saved', 'sum')
        ).reset_index()
        fig7 = px.scatter(
            financial_summary,
            x='Total_Investment', y='Total_Money_Saved',
            text='Comunidad Autónoma',
            size='Total_Investment',
            color='Comunidad Autónoma',
            title='Total Investment vs. Total Money Saved per Community',
            labels={'Total_Investment': 'Total Investment (€)', 'Total_Money_Saved': 'Total Money Saved (€)'}
        )
        fig7.update_traces(textposition='top center')
        st.plotly_chart(fig7, use_container_width=True)


    # --- Extra Charts (Specific for Madrid or other selections) ---
    if selected_community == 'Madrid':
        st.markdown("---")
        st.subheader("Detailed Analysis for Madrid")
        df_madrid = df_filtered.copy()
        
        total_energy_saved_madrid = df_madrid['Energy Saved'].sum()
        if total_energy_saved_madrid > 0:
            df_madrid['Energy_Saving_Percent'] = (df_madrid['Energy Saved'] / total_energy_saved_madrid) * 100
        else:
            df_madrid['Energy_Saving_Percent'] = 0

        extra_fig1 = px.scatter(
            df_madrid,
            x='Investment', y='Energy_Saving_Percent',
            hover_data=['Measure', 'Center'],
            title='Investment vs. Contribution to Energy Savings (Madrid)',
            labels={'Investment': 'Investment (€)', 'Energy_Saving_Percent': 'Contribution to Madrid\'s Energy Savings (%)'}
        )
        st.plotly_chart(extra_fig1, use_container_width=True)

else:
    st.warning("Data could not be loaded. Please check the file path and try again.")
