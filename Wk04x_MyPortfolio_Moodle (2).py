# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.19.10",
#     "pandas>=2.3.3",
#     "plotly>=6.5.1",
#     "pyarrow>=22.0.0",
#     "pyzmq>=27.1.0",
# ]
# ///

import marimo

__generated_with = "0.19.11"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import micropip
    return micropip, mo, pd


@app.cell
def _(pd):
    # 1: Setup & Data Prep

    csv_url = "https://gist.githubusercontent.com/DrAYim/80393243abdbb4bfe3b45fef58e8d3c8/raw/ed5cfd9f210bf80cb59a5f420bf8f2b88a9c2dcd/sp500_ZScore_AvgCostofDebt.csv"

    df_final = pd.read_csv(csv_url)

    df_final = df_final.dropna(subset=['AvgCost_of_Debt', 'Z_Score_lag', 'Sector_Key'])
    df_final = df_final[(df_final['AvgCost_of_Debt'] < 5)]
    df_final['Debt_Cost_Percent'] = df_final['AvgCost_of_Debt'] * 100
    df_final['Market_Cap_B'] = df_final['Market_Cap'] / 1e9
    return (df_final,)


@app.cell
def _(df_final, mo):
    # 2: Define the UI Controls

    all_sectors = sorted(df_final['Sector_Key'].unique().tolist())
    sector_dropdown = mo.ui.multiselect(
        options=all_sectors,
        value=all_sectors[:5],
        label="Filter by Sector",
    )

    cap_slider = mo.ui.slider(
        start=0,
        stop=200,
        step=10,
        value=0,
        label="Min Market Cap ($ Billions)"
    )
    return cap_slider, sector_dropdown


@app.cell
def _(cap_slider, df_final, sector_dropdown):
    # 3: Reactive Filter Logic

    filtered_portfolio = df_final[
        (df_final['Sector_Key'].isin(sector_dropdown.value)) &
        (df_final['Market_Cap_B'] >= cap_slider.value)
    ]

    count = len(filtered_portfolio)
    return count, filtered_portfolio


@app.cell
async def _(micropip):
    await micropip.install('plotly')
    import plotly.express as px
    return (px,)


@app.cell
def _(cap_slider, count, filtered_portfolio, mo, pd, px, sector_dropdown):
    # 4: Visualizations

    # =============================================
    # Plot 1: Treemap — Market Cap weighted by Cost of Debt
    # =============================================

    # Filter out rows with zero/missing Market Cap for a clean treemap
    df_treemap = filtered_portfolio[filtered_portfolio['Market_Cap_B'] > 0].copy()

    fig_treemap = px.treemap(
        df_treemap,
        path=['Sector_Key', 'Name'],
        values='Market_Cap_B',
        color='Debt_Cost_Percent',
        color_continuous_scale='RdYlGn_r',   # Red = expensive debt, Green = cheap debt
        color_continuous_midpoint=df_treemap['Debt_Cost_Percent'].median(),
        title=f"S&P 500 Market Cap — Coloured by Avg. Cost of Debt (%) | {count} companies",
        labels={
            'Market_Cap_B': 'Market Cap ($B)',
            'Debt_Cost_Percent': 'Avg. Cost of Debt (%)'
        },
        template='presentation',
        width=950,
        height=620,
    )

    fig_treemap.update_traces(
        textinfo="label+value",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Market Cap: $%{value:.1f}B<br>"
            "Avg. Cost of Debt: %{color:.2f}%<extra></extra>"
        )
    )

    fig_treemap.update_layout(
        coloraxis_colorbar=dict(title="Cost of<br>Debt (%)")
    )

    treemap_element = mo.ui.plotly(fig_treemap)

    # =============================================
    # Plot 2: Fitness — Weekly Running Distance Line Chart
    # =============================================

    # Mock data: weekly running distance (km) over 52 weeks, split by activity type
    import numpy as np
    rng = np.random.default_rng(42)

    weeks = list(range(1, 53))

    # Simulate realistic training: easy runs ~5km, long runs ~10km, rest weeks dip
    easy_base   = 5  + rng.normal(0, 0.8, 52)
    long_base   = 10 + rng.normal(0, 1.2, 52)
    interval_base = 7 + rng.normal(0, 1.0, 52)

    # Add a "peak season" ramp-up around weeks 20-35 (pre-season football)
    season_boost = np.where((np.array(weeks) >= 20) & (np.array(weeks) <= 35), 2.5, 0)

    df_fitness = pd.DataFrame({
        'Week': weeks * 3,
        'Distance_km': np.concatenate([
            np.clip(easy_base + season_boost, 2, 15),
            np.clip(long_base + season_boost, 5, 18),
            np.clip(interval_base + season_boost, 4, 14),
        ]),
        'Activity': ['Easy Run'] * 52 + ['Long Run'] * 52 + ['Interval / Speed'] * 52
    })

    fig_fitness = px.line(
        df_fitness,
        x='Week',
        y='Distance_km',
        color='Activity',
        markers=True,
        title='Weekly Running Distance by Training Type (2024–25)',
        labels={'Distance_km': 'Distance (km)', 'Week': 'Week of Year'},
        template='presentation',
        width=950,
        height=550,
        color_discrete_map={
            'Easy Run':         '#3A86FF',
            'Long Run':         '#FF006E',
            'Interval / Speed': '#FB5607',
        }
    )

    fig_fitness.add_vrect(
        x0=20, x1=35,
        fillcolor='rgba(255,165,0,0.12)',
        layer='below',
        line_width=0,
        annotation_text="Pre-season block",
        annotation_position="top left",
        annotation_font_size=12,
        annotation_font_color="darkorange"
    )

    fig_fitness.update_traces(marker=dict(size=4), line=dict(width=2))
    fig_fitness.update_layout(legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

    fitness_element = mo.ui.plotly(fig_fitness)

    return cap_slider, count, df_treemap, df_fitness, fig_fitness, fig_treemap, fitness_element, sector_dropdown, treemap_element


@app.cell
def _(cap_slider, fitness_element, mo, sector_dropdown, treemap_element):
    # 5: Define Tab Content

    # ─── Tab 1: About Me ───
    tab_cv = mo.md(
        """
        ### Aspiring Financial Analyst | Python & Data Enthusiast

        **Summary**

        BSc Accounting and Finance student at Bayes Business School, City, University of London, 
        with hands-on experience in investment analysis and financial modelling gained at the 
        Qatar Investment Authority. Strong foundation in Python, Excel, and quantitative methods; 
        passionate about applying data science tools to real-world finance problems.

        ---

        **Education**

        🏛️ **BSc Accounting and Finance** — Bayes Business School, City, University of London *(Sept 2025 – June 2028)*

        - *Financial Accounting (1st)* — financial statements, IFRS principles, valuation adjustments  
        - *Financial Institutions (1st)* — banks, central banks, regulation, financial instruments

        🏫 **Sherborne School** *(Sept 2012 – June 2024)*

        - A-Levels: Arabic, English General, Travel & Tourism  
        - IGCSEs: Maths, ICT, English, Travel & Tourism

        ---

        **Experience**

        💼 **Finance Intern — Qatar Investment Authority (QIA)** *(June – August 2024)*

        - Analysed financial statements and prepared ratio analysis summaries for potential portfolio companies  
        - Gathered market data, compared asset performance, and helped draft investment memos  
        - Built Excel valuation models (DCF and comparables) alongside senior analysts

        📊 **Treasurer — Business & Finance Society, Sherborne School** *(Sept 2022 – June 2023)*

        - Managed the society's annual budget, tracked expenses, and oversaw event payments  
        - Planned cash-flow for competitions and workshops; gained budgeting and forecasting experience

        ---

        **Skills**

        - 🐍 Python (Pandas, NumPy, Plotly, Marimo)  
        - 📊 Advanced Excel (pivot tables, VLOOKUP/XLOOKUP, DCF modelling)  
        - 🗄️ SQL (basic queries) · R (basic)  
        - 📑 Financial Statement Analysis · Ratio Analysis · Valuation (DCF, Comparables)
        """
    )

    # ─── Tab 2: Passion Projects ───
    tab_data_content = mo.vstack([
        mo.md("## 📊 Interactive Credit Risk Analyser"),
        mo.callout(
            mo.md(
                "**Treemap View:** Box size = Market Cap · Colour = Avg. Cost of Debt (%)  \n"
                "Red = more expensive debt · Green = cheaper debt. Use filters to explore sectors."
            ),
            kind="info"
        ),
        mo.hstack([sector_dropdown, cap_slider], justify="center", gap=2),
        treemap_element,
    ])

    # ─── Tab 3: Hobbies ───
    tab_personal = mo.vstack([
        mo.md("## 🏃 My Hobby: Football & Running"),
        mo.callout(
            mo.md(
                "I played in the school football team and keep fit year-round with structured running.  \n"
                "The chart below tracks weekly distances across three session types.  \n"
                "The **orange shaded region** marks the pre-season training block (weeks 20–35)."
            ),
            kind="success"
        ),
        fitness_element,
    ])

    return tab_cv, tab_data_content, tab_personal


@app.cell
def _(mo, tab_cv, tab_data_content, tab_personal):
    # 6: Assemble the Portfolio

    app_tabs = mo.ui.tabs({
        "📄 About Me":          tab_cv,
        "📊 Passion Projects":  tab_data_content,
        "🏃 Fitness & Sport":   tab_personal,
    })

    mo.md(
        f"""
        # **Nasser Al-Thani**
        *BSc Accounting & Finance · Bayes Business School · nasser.al-thani.6@bayes.city.ac.uk*

        ---
        {app_tabs}
        """
    )
    return


if __name__ == "__main__":
    app.run()