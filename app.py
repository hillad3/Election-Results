import pandas as pd
import numpy as np
import plotly.express as px
import itertools
import math
from dash import Dash, html, dcc, callback, Input, Output
import dash_daq as daq
from list_of_states import States

fig_dummy = px.scatter(
    x = None,
    y = None,
).update_xaxes(
    visible=False
).update_yaxes(
    visible=False
).add_annotation(
    dict(
        font=dict(size=20),
        x=0,
        y=0,
        text="Loading...",
        showarrow=False
    )
)

df_original = pd.read_csv(
    "compiled_fed_elections_2004-2024.csv",
    dtype={"State": str, "Year": str, "Candidate": str, "Party": str, "Votes": int},
)

# remove all totals for the states-only df
df_states = df_original.loc[
    (df_original["Candidate"] != "Total") & 
    (df_original["State"] != "Total") & 
    (df_original["Party"] != "Total")
]

colors = {"Democrat": "#00AEF3", "Republican": "#E9141D", "Third Party": "#007D10"}

app = Dash(__name__, prevent_initial_callbacks=True)

server = app.server


@app.callback(
    Output(component_id="us_vote_graph", component_property="figure"),
    [
        Input(component_id="toggle_votes_or_pct", component_property="n_clicks"),
        Input(component_id="toggle_states_or_all", component_property="n_clicks"),
        Input(component_id="states_selected", component_property="value"),
        Input(component_id="years_selected", component_property="value"),
        Input(component_id="parties_selected", component_property="value"),
        Input(component_id="facet_wrap_column_selector", component_property="value"),
    ],
)
def update_us_vote_graph(
    toggle_votes,
    toggle_states,
    states_selected,
    years_selected,
    parties_selected,
    facet_wrap_size,
):
    updated_df = (df_states.loc[
        (df_states["State"].isin(states_selected)) & 
        (df_states["Year"].isin(years_selected)) &
        (df_states["Party"].isin(parties_selected))
    ])

    if toggle_states & 1:
        updated_df = (
            updated_df
            .groupby(by=["Candidate","Party","Year"], as_index=False)
            .Votes
            .agg(Votes="sum")
            .sort_values(by = ["Year","Party"])
        )

    def get_y_range_max(df, is_total_us):
        if is_total_us:
            divisor = 100_000_000
            try:
                y_range_max = (
                    math.ceil(
                        max(
                            df
                            .groupby(by=["Year"])
                            .Votes
                            .sum()
                        )
                        / divisor
                    )
                    * divisor
                )
            except ValueError:  # covers when user unselects all states
                y_range_max = divisor
        else:
            divisor = 10_000_000
            try:
                y_range_max = (
                    math.ceil(
                        max(
                            df
                            .groupby(by=[df["State"], df["Year"]])
                            .Votes
                            .sum()
                        )
                        / divisor
                    )
                    * divisor
                )
            except ValueError:  # covers when user unselects all states
                y_range_max = divisor

        return y_range_max


    if toggle_votes & 1:  # this uses bitwise evaluation
        barnorm_setting = ""
    else:
        barnorm_setting = "percent"

    if barnorm_setting == "percent":
        y_range_max = 100
        if toggle_states & 1:
            subtitle_setting = f"Relative % of votes by Year"
        else:
            subtitle_setting = f"Relative % of votes by Year and State"

    else:
        if toggle_states & 1:
            y_range_max = get_y_range_max(updated_df, is_total_us=True)
            subtitle_setting = f"Votes by Year"
        else:
            y_range_max = get_y_range_max(updated_df, is_total_us=False)
            subtitle_setting = f"Votes by Year and State"

    if toggle_states & 1:
        
        if toggle_votes & 1:
            make_hovertemplate = "<b>Votes: %{y:,.0f}</b>"
        else:
            make_hovertemplate = "<b>Vote Share: %{y:,.1f}%</b>"

        fig = (
            px.histogram(
                data_frame=updated_df,
                x="Year",
                y="Votes",
                color="Party",
                color_discrete_map=colors,
                barnorm=barnorm_setting,
                height=400
            )
            .update_traces(
                customdata = np.stack((updated_df['Candidate']), axis=-1),
                hovertemplate=make_hovertemplate
            )
            .update_layout(
                title=dict(text="US Presidential Election, Popular Vote"),
                title_subtitle=dict(text=subtitle_setting),
                margin=dict(t=100),
                hovermode="x",
            )
            .update_xaxes(title=dict(font=dict(size=8)))
            .update_yaxes(range=[0, y_range_max])
            .for_each_annotation(
                lambda x: x.update(
                    text=x.text.split("=")[-1]
                )  # removes the "state=" from xaxis title
            )
            .for_each_xaxis(
                lambda x: x.update(
                    title=["" for i in itertools.repeat("", facet_wrap_size)][0]
                )
            )
            .for_each_yaxis(lambda x: x.update(title=""))
        )

        return fig
        
    else:

        if toggle_votes & 1:
            make_hovertemplate = "<b>Votes: %{y:,.0f}</b>"
        else:
            make_hovertemplate = "<b>Vote Share: %{y:,.1f}%</b>"

        fig = (
            px.histogram(
                data_frame=updated_df,
                x="Year",
                y="Votes",
                color="Party",
                color_discrete_map=colors,
                barnorm=barnorm_setting,
                facet_col="State",
                facet_col_wrap=facet_wrap_size,
                height=1200,
                facet_row_spacing=0.02
            )
            .update_traces(
                hovertemplate=make_hovertemplate
            )
            .update_layout(
                title=dict(text="US Presidential Election, Popular Vote"),
                title_subtitle=dict(text=subtitle_setting),
                margin=dict(t=100),
                hovermode="x",
            )
            .update_xaxes(title=dict(font=dict(size=8)))
            .update_yaxes(
                range=[0, y_range_max],
                tickvals=[0,y_range_max/2, y_range_max]
            )
            .for_each_annotation(
                lambda x: x.update(
                    text=x.text.split("=")[-1]
                )  # removes the "state=" from xaxis title
            )
            .for_each_xaxis(
                lambda x: x.update(
                    title=["" for i in itertools.repeat("", facet_wrap_size)][0]
                )
            )
            .for_each_yaxis(lambda x: x.update(title=""))
        )

        return fig

    
# updates the toggle states button with current state name
@callback(
    Output(component_id="toggle_states_or_all", component_property="children"),
    Input(component_id="toggle_states_or_all", component_property="n_clicks"),
)
def update_toggle(toggle_states):
    if toggle_states & 1:
        return "By USA"
    else:
        return "By State"
    

# updates the toggle votes button with the current state name
@callback(
    Output(component_id="toggle_votes_or_pct", component_property="children"),
    Input(component_id="toggle_votes_or_pct", component_property="n_clicks"),
)
def update_toggle(toggle_vote_clicks):
    if toggle_vote_clicks & 1:
        return "By Votes"
    else:
        return "By Pct."
    

# updates the states dropdown with all 50 states except DC
@callback(
    Output(component_id="states_selected", component_property="value"),
    Input(component_id="add_all_states", component_property="n_clicks"),
)
def add_all_states(n_clicks):
    return [state for state in States.state_code if state != "DC"]


# removes all states
@callback(
    Output(
        component_id="states_selected", component_property="value", allow_duplicate=True
    ),
    Input(component_id="remove_all_states", component_property="n_clicks"),
    prevent_initial_call=True,
)
def remove_all_states(n_clicks):
    return []


# add swing states
@callback(
    Output(
        component_id="states_selected", component_property="value", allow_duplicate=True
    ),
    Input(component_id="add_swing_states", component_property="n_clicks"),
    prevent_initial_call=True,
)
def add_swing_states(n_clicks):
    return [
        state
        for state in States.state_code
        if state in ["AZ", "GA", "MI", "NC", "NV", "PA", "WI"]
    ]


# updates the year with all years
@callback(
    Output(component_id="years_selected", component_property="value"),
    Input(component_id="add_all_years", component_property="n_clicks"),
)
def add_all_years(n_clicks):
    return ["2004", "2008", "2012", "2016", "2020", "2024"]


# removes all years from the data set
@callback(
    Output(
        component_id="years_selected", component_property="value", allow_duplicate=True
    ),
    Input(component_id="remove_all_years", component_property="n_clicks"),
    prevent_initial_call=True,
)
def remove_all_years(n_clicks):
    return []


# Dash Layout
app.layout = [
    html.Div(
        [
            html.Title("US Presidential Election Results, 2004-2024"),
            html.H1(
                "Explore US Presidential Election Results, 2004-2024",
                style={"text-align": "center", "margin-top": "50px"},
            ),
            html.P(
                html.Span(
                    [
                        "The 2024 general election has not been officially reported by all states, so minor vote tally changes are possible. "
                        "2024 tallies are based on ",
                        html.A(
                            "AP News",
                            href="https://apnews.com/projects/election-results-2024/",
                            style={"color": "#2391be"},
                        ),
                        " as of 28-Nov-2024. ",
                        "The remaining vote tallies are based on the ",
                        html.A(
                            "Federal Election Commission reports",
                            href="https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/#election-results",
                            style={"color": "#2391be"},
                        ),
                        ".",
                    ]
                )
            ),
        ],
        className="header-box",
    ),
    html.Div(
        [
            html.H4("Toggle Options"),
            html.Button(
                children="Toggle States",
                id="toggle_states_or_all",
                n_clicks=0,
                className="btn btn-danger",
                style={"width": "20%", "margin-right": "0.25rem"},
            ),
            html.Button(
                children="Toggle Votes",
                id="toggle_votes_or_pct",
                n_clicks=0,
                className="btn btn-primary",
                style={"width": "20%", "margin-left": "0.25rem"},
            ),

        ],
        className="selector-box",
    ),
    html.Div(
        dcc.Graph(figure=fig_dummy, id="us_vote_graph"),
    ),
    html.Div(
        [
            html.H4("States Selected"),
            dcc.Dropdown(
                options=[state for state in States.state_code if state != "DC"],
                value=[state for state in States.state_code if state != "DC"],
                id="states_selected",
                multi=True,
            ),
            html.Button(
                "Add All",
                id="add_all_states",
                n_clicks=0,
                className="btn btn-primary",
                style={
                    "margin-right": "0.25rem",
                    "margin-top": "0.5rem",
                    "width": "7rem",
                },
            ),
            html.Button(
                "Remove All",
                id="remove_all_states",
                n_clicks=0,
                className="btn btn-danger",
                style={
                    "margin-left": "0.25rem",
                    "margin-right": "0.25rem",
                    "margin-top": "0.5rem",
                    "width": "7rem",
                },
            ),
            html.Button(
                "2024 Swing States",
                id="add_swing_states",
                n_clicks=0,
                className="btn btn-info",
                style={
                    "margin-left": "0.25rem",
                    "margin-right": "0.25rem",
                    "margin-top": "0.5rem",
                    "width": "10rem",
                },
            ),
        ],
        className="selector-box",
    ),
    html.Div(
        [
            html.H4("Years Selected"),
            dcc.Dropdown(
                options=["2004", "2008", "2012", "2016", "2020", "2024"],
                value=["2004", "2008", "2012", "2016", "2020", "2024"],
                id="years_selected",
                multi=True,
            ),
            html.Button(
                "Add All",
                id="add_all_years",
                n_clicks=0,
                className="btn btn-primary",
                style={
                    "margin-right": "0.25rem",
                    "margin-top": "0.5rem",
                    "width": "7rem",
                },
            ),
            html.Button(
                "Remove All",
                id="remove_all_years",
                n_clicks=0,
                className="btn btn-danger",
                style={
                    "margin-left": "0.25rem",
                    "margin-top": "0.5rem",
                    "width": "7rem",
                },
            ),
        ],
        className="selector-box",
    ),
    html.Div(
        [
            html.H4("Parties Selected"),
            dcc.Dropdown(
                options=["Democrat", "Republican", "Third Party"],
                value=["Democrat", "Republican", "Third Party"],
                id="parties_selected",
                multi=True,
            ),
        ],
        className="selector-box",
    ),
    html.Div(
        [
            html.H4("Max Columns"),
            daq.NumericInput(id="facet_wrap_column_selector", value=5, min=1, max=20),
        ],
        className="selector-box",
    ),
]

if __name__ == "__main__":
    app.run(debug=True)
