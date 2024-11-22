import pandas as pd
import numpy as np
import plotly.express as px
import itertools
import math
from dash import Dash, html, dcc, callback, Input, Output
import dash_daq as daq
from list_of_states import States

df = pd.read_csv(
    "compiled_fed_elections_2004-2024.csv",
    dtype={"State": str, "Year": str, "Candidate": str, "Party": str, "Votes": int},
)

df_states = df.loc[(df["Candidate"] != "Total") & (df["State"] != "Total")]

DEM_COLOR = "#00AEF3"
REP_COLOR = "#E9141D"
OTH_COLOR = "#007D10"

app = Dash(__name__, prevent_initial_callbacks=True)


@app.callback(
    Output(component_id="ge_pop_vote_graph", component_property="figure"),
    [
        Input(component_id="facet_wrap_column_selector", component_property="value"),
        Input(component_id="toggle_votes_or_pct", component_property="n_clicks"),
        Input(component_id="states_selected", component_property="value"),
        Input(component_id="years_selected", component_property="value"),
        Input(component_id="parties_selected", component_property="value"),
    ],
)
def update_ge_vote_graph(
    facet_wrap_size, toggle_votes, states_selected, years_selected, parties_selected
):

    updated_df = df_states.loc[(df_states["State"].isin(states_selected))]
    updated_df = updated_df.loc[(updated_df["Year"].isin(years_selected))]
    updated_df = updated_df.loc[(updated_df["Party"].isin(parties_selected))]

    if toggle_votes & 1:  # this uses bitwise evaluation
        barnorm_setting = ""
    else:
        barnorm_setting = "percent"

    if barnorm_setting == "percent":
        y_range_max = 100
        subtitle_setting = r"% of total votes by Year and State"
    else:

        try:
            y_range_max = (
                math.ceil(
                    max(
                        updated_df.loc[
                            (updated_df["Candidate"] != "Total")
                            & (updated_df["State"] != "Total"),
                            "Votes",
                        ]
                        .groupby(by=[updated_df["State"], updated_df["Year"]])
                        .sum()
                    )
                    / 10000000
                )
                * 10000000
            )
        except ValueError:  # covers when user unselects all states
            y_range_max = 10000000

        subtitle_setting = "Total votes by Year and State"

    fig = (
        px.histogram(
            data_frame=updated_df,
            x="Year",
            y="Votes",
            color="Party",
            color_discrete_sequence=[REP_COLOR, DEM_COLOR, OTH_COLOR],
            barnorm=barnorm_setting,
            facet_col="State",
            facet_col_wrap=facet_wrap_size
        )
        .update_layout(
            title=dict(text="US Presidental Election, Popular Vote"),
            title_subtitle=dict(text=subtitle_setting),
            margin=dict(t=100),
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
    return [state for state in States.state_code if state in ["AZ","GA","MI","NC","NV","PA","WI"]]


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


# updates the toggle button with the next toggle name
@callback(
    Output(component_id="toggle_votes_or_pct", component_property="children"),
    Input(component_id="toggle_votes_or_pct", component_property="n_clicks"),
)
def update_toggle(toggle_vote_clicks):
    if toggle_vote_clicks & 1:
        return "By Votes"
    else:
        return "By Percent"


# Dash Layout
app.layout = [
    html.Div(
        [    
            html.Title("US Presidental Election Results, 2004-2024"),
            html.H1("Explore US Presidental Election Results, 2004-2024", style={"text-align":"center", "margin-top":"50px"}),
            html.P(
                html.Span(
                    [
                        "The 2024 general election has not been officially reported by all states, so minor vote tally changes are possible. "
                        "2024 tallies are based on ",
                        html.A("AP News", href="https://apnews.com/projects/election-results-2024/", style={"color":"#2391be"}),
                        " as of 22-Nov-2024. ",
                        "The remaining vote tallies are based on the ",
                        html.A("Federal Election Commission reports", href="https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/#election-results", style={"color":"#2391be"}),
                        "."
                    ] 
                )
            )
        ],
        className="header-box"
    ),
    html.Div(
        dcc.Graph(figure={}, id="ge_pop_vote_graph"),
    ),
    html.Div(
        [
            html.H4("Vote Summary"),
            html.Button(
                children="Toggle Votes",
                id="toggle_votes_or_pct",
                n_clicks=0,
                className="btn btn-primary",
                style={"width": "14.5rem"},
            ),
        ],
        className="selector-box",
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
                options=["Democrat","Republican","Third Party"],
                value=["Democrat","Republican","Third Party"],
                id="parties_selected",
                multi=True,
            )
        ],
        className="selector-box",
    ),
    html.Div(
        [
            html.H4("Max Columns"),
            daq.NumericInput(id="facet_wrap_column_selector", value=10, min=1, max=20),
        ],
        className="selector-box",
    ),
]

if __name__ == "__main__":
    app.run(debug=True)
