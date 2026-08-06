from __future__ import annotations

from typing import Iterable, Optional

import numpy as np
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

from plotly.subplots import make_subplots


THEME = {
    "navy": "#081A2D",
    "navy_soft": "#102A43",
    "teal": "#0E7490",
    "teal_light": "#14B8A6",
    "blue": "#3B82F6",
    "amber": "#F59E0B",
    "red": "#DC2626",
    "purple": "#7C3AED",
    "green": "#16A34A",
    "background": "#F4F7FB",
    "card": "#FFFFFF",
    "text": "#172033",
    "muted": "#667085",
    "border": "#E4E7EC",
    "grid": "#E8EDF4"
}


EXPOSURE_COLOUR_MAP = {
    "No forecast exceedance": "#94A3B8",
    "Moderate exposure": "#3B82F6",
    "High exposure": "#F59E0B",
    "Very high exposure": "#DC2626"
}


COST_BAND_COLOUR_MAP = {
    "Zero cost day": "#94A3B8",
    "Positive cost day": "#0E7490",
    "High cost day": "#DC2626",
    "Cost unavailable": "#CBD5E1"
}


CLASSIFICATION_COLOUR_MAP = {
    "True negative": "#64748B",
    "False positive": "#F59E0B",
    "False negative": "#DC2626",
    "True positive": "#16A34A"
}


def _empty_figure(
    title: str,
    message: str = "No data are available for the selected filters."
) -> go.Figure:

    figure = go.Figure()

    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={
            "size": 15,
            "color": THEME["muted"]
        },
        align="center"
    )

    figure.update_layout(
        title=title,
        height=420
    )

    return apply_standard_layout(
        figure
    )


def apply_standard_layout(
    figure: go.Figure,
    height: int = 430,
    legend_orientation: str = "h"
) -> go.Figure:

    figure.update_layout(
        height=height,
        paper_bgcolor=THEME["card"],
        plot_bgcolor=THEME["card"],
        font={
            "family":
                "Inter, Segoe UI, Arial, sans-serif",

            "color":
                THEME["text"]
        },
        title={
            "font": {
                "size": 18,
                "color": THEME["text"]
            },
            "x": 0.01,
            "xanchor": "left"
        },
        margin={
            "l": 58,
            "r": 30,
            "t": 68,
            "b": 56
        },
        hoverlabel={
            "bgcolor": THEME["navy"],
            "font_color": "#FFFFFF",
            "font_size": 13
        },
        legend={
            "orientation": legend_orientation,
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1
        }
    )

    figure.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=THEME["border"],
        tickfont={
            "color": THEME["muted"]
        },
        title_font={
            "color": THEME["muted"]
        }
    )

    figure.update_yaxes(
        showgrid=True,
        gridcolor=THEME["grid"],
        zeroline=False,
        linecolor=THEME["border"],
        tickfont={
            "color": THEME["muted"]
        },
        title_font={
            "color": THEME["muted"]
        }
    )

    return figure


def _prepare_date_column(
    dataframe: pd.DataFrame,
    column_name: str
) -> pd.DataFrame:

    prepared = dataframe.copy()

    if column_name in prepared.columns:

        prepared[column_name] = pd.to_datetime(
            prepared[column_name],
            errors="coerce"
        )

    return prepared


def monthly_cost_exposure_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "Monthly thermal cost and forecast exposure"
        )

    prepared = _prepare_date_column(
        dataframe,
        "month_start_date"
    ).sort_values(
        "month_start_date"
    )

    figure = make_subplots(
        specs=[
            [
                {
                    "secondary_y": True
                }
            ]
        ]
    )

    figure.add_trace(
        go.Bar(
            x=prepared["month_start_date"],
            y=prepared[
                "total_thermal_constraint_cost_gbp"
            ],
            name="Thermal constraint cost",
            marker_color=THEME["teal"],
            hovertemplate=(
                "%{x|%b %Y}<br>"
                "Cost: £%{y:,.0f}"
                "<extra></extra>"
            )
        ),
        secondary_y=False
    )

    figure.add_trace(
        go.Scatter(
            x=prepared["month_start_date"],
            y=prepared[
                "total_exceedance_volume_mwh"
            ],
            name="Forecast exceedance volume",
            mode="lines+markers",
            line={
                "color": THEME["amber"],
                "width": 3
            },
            marker={
                "size": 7
            },
            hovertemplate=(
                "%{x|%b %Y}<br>"
                "Exposure: %{y:,.0f} MWh equivalent"
                "<extra></extra>"
            )
        ),
        secondary_y=True
    )

    figure.update_layout(
        title=(
            "Monthly thermal cost and "
            "forecast exposure"
        ),
        barmode="group"
    )

    figure.update_yaxes(
        title_text="Thermal constraint cost, GBP",
        tickprefix="£",
        separatethousands=True,
        secondary_y=False
    )

    figure.update_yaxes(
        title_text="Forecast exposure, MWh equivalent",
        separatethousands=True,
        secondary_y=True,
        showgrid=False
    )

    return apply_standard_layout(
        figure,
        height=460
    )


def cost_outcome_mix_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if (
        dataframe is None
        or dataframe.empty
        or "thermal_cost_band" not in dataframe.columns
    ):

        return _empty_figure(
            "Daily cost outcome mix"
        )

    summary = (
        dataframe[
            "thermal_cost_band"
        ]
        .fillna("Cost unavailable")
        .value_counts()
        .rename_axis("thermal_cost_band")
        .reset_index(name="day_count")
    )

    figure = px.pie(
        summary,
        names="thermal_cost_band",
        values="day_count",
        hole=0.67,
        color="thermal_cost_band",
        color_discrete_map=COST_BAND_COLOUR_MAP
    )

    figure.update_traces(
        textposition="outside",
        textinfo="percent+label",
        hovertemplate=(
            "%{label}<br>"
            "Days: %{value:,}<br>"
            "Share: %{percent}"
            "<extra></extra>"
        )
    )

    figure.add_annotation(
        text=(
            f"<b>{int(summary['day_count'].sum()):,}</b>"
            "<br><span style='font-size:12px'>days</span>"
        ),
        x=0.5,
        y=0.5,
        showarrow=False,
        font={
            "size": 20,
            "color": THEME["text"]
        }
    )

    figure.update_layout(
        title="Daily cost outcome mix",
        showlegend=False
    )

    return apply_standard_layout(
        figure,
        height=440
    )


def daily_constraint_cost_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "Daily thermal constraint cost"
        )

    prepared = _prepare_date_column(
        dataframe,
        "settlement_date"
    ).sort_values(
        "settlement_date"
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=prepared["settlement_date"],
            y=prepared[
                "thermal_constraint_cost_gbp"
            ],
            mode="lines",
            name="Daily cost",
            line={
                "color": THEME["teal"],
                "width": 2
            },
            fill="tozeroy",
            fillcolor="rgba(14, 116, 144, 0.13)",
            hovertemplate=(
                "%{x|%d %b %Y}<br>"
                "Cost: £%{y:,.0f}"
                "<extra></extra>"
            )
        )
    )

    high_cost_rows = prepared.loc[
        prepared[
            "high_cost_event_definition"
        ].fillna(0).astype(int).eq(1)
    ]

    if not high_cost_rows.empty:

        figure.add_trace(
            go.Scatter(
                x=high_cost_rows["settlement_date"],
                y=high_cost_rows[
                    "thermal_constraint_cost_gbp"
                ],
                mode="markers",
                name="High cost day",
                marker={
                    "color": THEME["red"],
                    "size": 8,
                    "line": {
                        "color": "#FFFFFF",
                        "width": 1
                    }
                },
                hovertemplate=(
                    "%{x|%d %b %Y}<br>"
                    "High cost: £%{y:,.0f}"
                    "<extra></extra>"
                )
            )
        )

    figure.update_layout(
        title="Daily thermal constraint cost"
    )

    figure.update_yaxes(
        title="Realised cost, GBP",
        tickprefix="£",
        separatethousands=True
    )

    return apply_standard_layout(
        figure,
        height=460
    )


def cumulative_constraint_cost_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "Cumulative thermal constraint cost"
        )

    prepared = _prepare_date_column(
        dataframe,
        "settlement_date"
    ).sort_values(
        "settlement_date"
    )

    prepared[
        "cumulative_thermal_constraint_cost_gbp"
    ] = (
        pd.to_numeric(
            prepared[
                "thermal_constraint_cost_gbp"
            ],
            errors="coerce"
        )
        .fillna(0)
        .cumsum()
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=prepared["settlement_date"],
            y=prepared[
                "cumulative_thermal_constraint_cost_gbp"
            ],
            mode="lines",
            name="Cumulative cost",
            line={
                "color": THEME["blue"],
                "width": 3
            },
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.10)",
            hovertemplate=(
                "%{x|%d %b %Y}<br>"
                "Cumulative cost: £%{y:,.0f}"
                "<extra></extra>"
            )
        )
    )

    figure.update_layout(
        title="Cumulative thermal constraint cost"
    )

    figure.update_yaxes(
        title="Cumulative realised cost, GBP",
        tickprefix="£",
        separatethousands=True
    )

    return apply_standard_layout(
        figure,
        height=440
    )


def exposure_calendar_heatmap_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "Forecast exposure calendar"
        )

    prepared = _prepare_date_column(
        dataframe,
        "settlement_date"
    )

    prepared = prepared.dropna(
        subset=[
            "settlement_date"
        ]
    ).copy()

    prepared[
        "week_start"
    ] = (
        prepared["settlement_date"]
        -
        pd.to_timedelta(
            prepared[
                "settlement_date"
            ].dt.weekday,
            unit="D"
        )
    )

    prepared[
        "day_order"
    ] = prepared[
        "settlement_date"
    ].dt.weekday

    prepared[
        "day_name"
    ] = prepared[
        "settlement_date"
    ].dt.day_name().str.slice(
        0,
        3
    )

    pivot = prepared.pivot_table(
        index="day_order",
        columns="week_start",
        values="total_exceedance_volume_mwh",
        aggfunc="sum"
    ).reindex(
        range(7)
    )

    day_labels = [
        "Mon",
        "Tue",
        "Wed",
        "Thu",
        "Fri",
        "Sat",
        "Sun"
    ]

    figure = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=day_labels,
            colorscale=[
                [0.00, "#EFF6FF"],
                [0.25, "#BAE6FD"],
                [0.50, "#38BDF8"],
                [0.75, "#F59E0B"],
                [1.00, "#DC2626"]
            ],
            colorbar={
                "title":
                    "MWh<br>equivalent"
            },
            hovertemplate=(
                "Week: %{x|%d %b %Y}<br>"
                "Day: %{y}<br>"
                "Exposure: %{z:,.0f} MWh equivalent"
                "<extra></extra>"
            )
        )
    )

    figure.update_layout(
        title="Forecast exposure calendar"
    )

    figure.update_yaxes(
        autorange="reversed",
        title=None
    )

    figure.update_xaxes(
        title="Week commencing"
    )

    return apply_standard_layout(
        figure,
        height=420
    )


def monthly_cost_ranking_figure(
    dataframe: pd.DataFrame,
    top_n: int = 12
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "Highest cost months"
        )

    prepared = _prepare_date_column(
        dataframe,
        "month_start_date"
    )

    prepared[
        "month_label"
    ] = prepared[
        "month_start_date"
    ].dt.strftime(
        "%b %Y"
    )

    ranking = (
        prepared
        .nlargest(
            top_n,
            "total_thermal_constraint_cost_gbp"
        )
        .sort_values(
            "total_thermal_constraint_cost_gbp"
        )
    )

    figure = go.Figure(
        go.Bar(
            x=ranking[
                "total_thermal_constraint_cost_gbp"
            ],
            y=ranking["month_label"],
            orientation="h",
            marker={
                "color":
                    ranking[
                        "total_thermal_constraint_cost_gbp"
                    ],
                "colorscale": [
                    [0, "#BAE6FD"],
                    [1, THEME["teal"]]
                ]
            },
            text=ranking[
                "total_thermal_constraint_cost_gbp"
            ].map(
                lambda value:
                    f"£{value / 1_000_000:.1f}m"
            ),
            textposition="outside",
            hovertemplate=(
                "%{y}<br>"
                "Cost: £%{x:,.0f}"
                "<extra></extra>"
            )
        )
    )

    figure.update_layout(
        title="Highest cost months"
    )

    figure.update_xaxes(
        title="Total realised cost, GBP",
        tickprefix="£",
        separatethousands=True
    )

    figure.update_yaxes(
        title=None
    )

    return apply_standard_layout(
        figure,
        height=470
    )


def financial_year_comparison_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "Financial year cost comparison"
        )

    prepared = dataframe.dropna(
        subset=[
            "financial_year"
        ]
    ).copy()

    if prepared.empty:

        return _empty_figure(
            "Financial year cost comparison"
        )

    summary = (
        prepared
        .groupby(
            "financial_year",
            as_index=False
        )
        .agg(
            total_cost_gbp=(
                "thermal_constraint_cost_gbp",
                "sum"
            ),
            high_cost_days=(
                "high_cost_event_definition",
                "sum"
            ),
            daily_records=(
                "settlement_date",
                "count"
            )
        )
    )

    figure = make_subplots(
        specs=[
            [
                {
                    "secondary_y": True
                }
            ]
        ]
    )

    figure.add_trace(
        go.Bar(
            x=summary["financial_year"],
            y=summary["total_cost_gbp"],
            name="Total cost",
            marker_color=THEME["teal"],
            hovertemplate=(
                "%{x}<br>"
                "Cost: £%{y:,.0f}"
                "<extra></extra>"
            )
        ),
        secondary_y=False
    )

    figure.add_trace(
        go.Scatter(
            x=summary["financial_year"],
            y=summary["high_cost_days"],
            name="High cost days",
            mode="lines+markers",
            line={
                "color": THEME["red"],
                "width": 3
            },
            marker={
                "size": 9
            },
            hovertemplate=(
                "%{x}<br>"
                "High cost days: %{y:,.0f}"
                "<extra></extra>"
            )
        ),
        secondary_y=True
    )

    figure.update_layout(
        title="Financial year cost comparison"
    )

    figure.update_yaxes(
        title="Total realised cost, GBP",
        tickprefix="£",
        separatethousands=True,
        secondary_y=False
    )

    figure.update_yaxes(
        title="High cost days",
        secondary_y=True,
        showgrid=False
    )

    return apply_standard_layout(
        figure,
        height=440
    )


def exceedance_cost_scatter_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "Forecast exceedance volume versus realised cost"
        )

    figure = px.scatter(
        dataframe,
        x="total_exceedance_volume_mwh",
        y="thermal_constraint_cost_gbp",
        color="forecast_exposure_band",
        size="forecast_exceedance_groups",
        hover_data=[
            "settlement_date",
            "maximum_single_period_exceedance_mw",
            "maximum_group_peak_utilisation_pct",
            "thermal_cost_band"
        ],
        color_discrete_map=EXPOSURE_COLOUR_MAP,
        opacity=0.76
    )

    figure.update_traces(
        marker={
            "line": {
                "color": "#FFFFFF",
                "width": 0.7
            }
        }
    )

    figure.update_layout(
        title=(
            "Forecast exceedance volume "
            "versus realised cost"
        )
    )

    figure.update_xaxes(
        title="Forecast exposure, MWh equivalent"
    )

    figure.update_yaxes(
        title="Realised thermal constraint cost, GBP",
        tickprefix="£",
        separatethousands=True
    )

    return apply_standard_layout(
        figure,
        height=500
    )


def exposure_band_cost_boxplot_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "Cost distribution by forecast exposure band"
        )

    order = [
        "No forecast exceedance",
        "Moderate exposure",
        "High exposure",
        "Very high exposure"
    ]

    figure = px.box(
        dataframe,
        x="forecast_exposure_band",
        y="thermal_constraint_cost_gbp",
        color="forecast_exposure_band",
        category_orders={
            "forecast_exposure_band":
                order
        },
        color_discrete_map=EXPOSURE_COLOUR_MAP,
        points="outliers"
    )

    figure.update_layout(
        title=(
            "Cost distribution by "
            "forecast exposure band"
        ),
        showlegend=False
    )

    figure.update_xaxes(
        title="Forecast exposure band"
    )

    figure.update_yaxes(
        title="Realised thermal constraint cost, GBP",
        tickprefix="£",
        separatethousands=True
    )

    return apply_standard_layout(
        figure,
        height=470
    )


def stress_correlation_heatmap_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "Stress and cost correlation matrix"
        )

    candidate_columns = [
        "forecast_exceedance_groups",
        "positive_direction_groups",
        "utilisation_90_groups",
        "total_positive_direction_periods",
        "total_exceedance_volume_mwh",
        "maximum_single_period_exceedance_mw",
        "maximum_group_peak_utilisation_pct",
        "thermal_constraint_cost_gbp"
    ]

    selected_columns = [
        column_name
        for column_name in candidate_columns
        if column_name in dataframe.columns
    ]

    if len(selected_columns) < 2:

        return _empty_figure(
            "Stress and cost correlation matrix"
        )

    numeric_data = dataframe[
        selected_columns
    ].apply(
        pd.to_numeric,
        errors="coerce"
    )

    correlation = numeric_data.corr(
        method="spearman"
    )

    label_lookup = {
        "forecast_exceedance_groups":
            "Exceedance groups",

        "positive_direction_groups":
            "Positive direction groups",

        "utilisation_90_groups":
            "Groups at or above 90%",

        "total_positive_direction_periods":
            "Positive direction periods",

        "total_exceedance_volume_mwh":
            "Exceedance volume",

        "maximum_single_period_exceedance_mw":
            "Peak period exceedance",

        "maximum_group_peak_utilisation_pct":
            "Peak utilisation",

        "thermal_constraint_cost_gbp":
            "Thermal cost"
    }

    labels = [
        label_lookup.get(
            column_name,
            column_name
        )
        for column_name in selected_columns
    ]

    figure = go.Figure(
        go.Heatmap(
            z=correlation.values,
            x=labels,
            y=labels,
            zmin=-1,
            zmax=1,
            colorscale=[
                [0.00, "#2563EB"],
                [0.50, "#F8FAFC"],
                [1.00, "#DC2626"]
            ],
            text=np.round(
                correlation.values,
                2
            ),
            texttemplate="%{text}",
            colorbar={
                "title":
                    "Spearman<br>correlation"
            },
            hovertemplate=(
                "%{y}<br>"
                "%{x}<br>"
                "Correlation: %{z:.3f}"
                "<extra></extra>"
            )
        )
    )

    figure.update_layout(
        title="Stress and cost correlation matrix"
    )

    figure.update_xaxes(
        tickangle=-35
    )

    return apply_standard_layout(
        figure,
        height=570
    )


def high_cost_rate_by_exposure_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "High cost event rate by exposure band"
        )

    summary = (
        dataframe
        .groupby(
            "forecast_exposure_band",
            as_index=False
        )
        .agg(
            observed_high_cost_rate=(
                "high_cost_event_definition",
                "mean"
            ),
            day_count=(
                "settlement_date",
                "count"
            )
        )
    )

    order = [
        "No forecast exceedance",
        "Moderate exposure",
        "High exposure",
        "Very high exposure"
    ]

    summary[
        "forecast_exposure_band"
    ] = pd.Categorical(
        summary[
            "forecast_exposure_band"
        ],
        categories=order,
        ordered=True
    )

    summary = summary.sort_values(
        "forecast_exposure_band"
    )

    figure = go.Figure(
        go.Bar(
            x=summary[
                "forecast_exposure_band"
            ],
            y=summary[
                "observed_high_cost_rate"
            ],
            marker_color=[
                EXPOSURE_COLOUR_MAP.get(
                    str(value),
                    THEME["teal"]
                )
                for value in summary[
                    "forecast_exposure_band"
                ]
            ],
            text=summary[
                "observed_high_cost_rate"
            ].map(
                lambda value:
                    f"{value:.1%}"
            ),
            customdata=summary[
                "day_count"
            ],
            textposition="outside",
            hovertemplate=(
                "%{x}<br>"
                "Observed high cost rate: %{y:.1%}<br>"
                "Days: %{customdata:,}"
                "<extra></extra>"
            )
        )
    )

    figure.update_layout(
        title=(
            "Observed high cost event rate "
            "by exposure band"
        )
    )

    figure.update_xaxes(
        title="Forecast exposure band"
    )

    figure.update_yaxes(
        title="Observed high cost event rate",
        tickformat=".0%",
        rangemode="tozero"
    )

    return apply_standard_layout(
        figure,
        height=440
    )


def historical_risk_timeline_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "Historical high cost risk score"
        )

    prepared = _prepare_date_column(
        dataframe,
        "settlement_date"
    ).sort_values(
        "settlement_date"
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=prepared["settlement_date"],
            y=prepared["high_cost_risk_score"],
            name="Risk score",
            mode="lines",
            line={
                "color": THEME["blue"],
                "width": 2
            },
            hovertemplate=(
                "%{x|%d %b %Y}<br>"
                "Risk score: %{y:.3f}"
                "<extra></extra>"
            )
        )
    )

    actual_event_rows = prepared.loc[
        prepared[
            "actual_high_cost_event"
        ].fillna(0).astype(int).eq(1)
    ]

    if not actual_event_rows.empty:

        figure.add_trace(
            go.Scatter(
                x=actual_event_rows[
                    "settlement_date"
                ],
                y=actual_event_rows[
                    "high_cost_risk_score"
                ],
                name="Actual high cost event",
                mode="markers",
                marker={
                    "color": THEME["red"],
                    "size": 9,
                    "symbol": "diamond",
                    "line": {
                        "color": "#FFFFFF",
                        "width": 1
                    }
                },
                hovertemplate=(
                    "%{x|%d %b %Y}<br>"
                    "Risk score: %{y:.3f}<br>"
                    "Actual high cost event"
                    "<extra></extra>"
                )
            )
        )

    threshold_series = pd.to_numeric(
        prepared[
            "risk_score_threshold"
        ],
        errors="coerce"
    ).dropna()

    if not threshold_series.empty:

        threshold_value = float(
            threshold_series.iloc[0]
        )

        figure.add_hline(
            y=threshold_value,
            line_dash="dash",
            line_color=THEME["amber"],
            annotation_text=(
                f"Fixed threshold {threshold_value:.2f}"
            ),
            annotation_position="top left"
        )

    figure.update_layout(
        title="Historical high cost risk score"
    )

    figure.update_yaxes(
        title="Empirical risk ranking score",
        range=[
            0,
            1
        ]
    )

    return apply_standard_layout(
        figure,
        height=470
    )


def classification_confusion_matrix_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "Historical classification outcomes"
        )

    actual = pd.to_numeric(
        dataframe[
            "actual_high_cost_event"
        ],
        errors="coerce"
    ).fillna(0).astype(int)

    predicted = pd.to_numeric(
        dataframe[
            "predicted_high_cost_event"
        ],
        errors="coerce"
    ).fillna(0).astype(int)

    matrix = pd.crosstab(
        actual,
        predicted
    ).reindex(
        index=[
            0,
            1
        ],
        columns=[
            0,
            1
        ],
        fill_value=0
    )

    figure = go.Figure(
        go.Heatmap(
            z=matrix.values,
            x=[
                "Predicted lower cost",
                "Predicted high cost"
            ],
            y=[
                "Actual lower cost",
                "Actual high cost"
            ],
            colorscale=[
                [0, "#EFF6FF"],
                [1, THEME["blue"]]
            ],
            text=matrix.values,
            texttemplate="%{text:,}",
            hovertemplate=(
                "%{y}<br>"
                "%{x}<br>"
                "Records: %{z:,}"
                "<extra></extra>"
            ),
            showscale=False
        )
    )

    figure.update_layout(
        title="Historical classification outcomes"
    )

    figure.update_yaxes(
        autorange="reversed"
    )

    return apply_standard_layout(
        figure,
        height=430
    )


def score_band_event_rate_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "Observed high cost rate by risk score band"
        )

    summary = (
        dataframe
        .groupby(
            "risk_score_band",
            as_index=False
        )
        .agg(
            observed_event_rate=(
                "actual_high_cost_event",
                "mean"
            ),
            record_count=(
                "settlement_date",
                "count"
            )
        )
    )

    order = [
        "0.00 to 0.20",
        "0.20 to 0.40",
        "0.40 to 0.60",
        "0.60 to 0.80",
        "0.80 to 1.00"
    ]

    summary[
        "risk_score_band"
    ] = pd.Categorical(
        summary[
            "risk_score_band"
        ],
        categories=order,
        ordered=True
    )

    summary = summary.sort_values(
        "risk_score_band"
    )

    figure = make_subplots(
        specs=[
            [
                {
                    "secondary_y": True
                }
            ]
        ]
    )

    figure.add_trace(
        go.Bar(
            x=summary["risk_score_band"],
            y=summary["observed_event_rate"],
            name="Observed event rate",
            marker_color=THEME["purple"],
            text=summary[
                "observed_event_rate"
            ].map(
                lambda value:
                    f"{value:.1%}"
            ),
            textposition="outside",
            hovertemplate=(
                "%{x}<br>"
                "Observed event rate: %{y:.1%}"
                "<extra></extra>"
            )
        ),
        secondary_y=False
    )

    figure.add_trace(
        go.Scatter(
            x=summary["risk_score_band"],
            y=summary["record_count"],
            name="Records",
            mode="lines+markers",
            line={
                "color": THEME["teal"],
                "width": 3
            },
            marker={
                "size": 8
            },
            hovertemplate=(
                "%{x}<br>"
                "Records: %{y:,}"
                "<extra></extra>"
            )
        ),
        secondary_y=True
    )

    figure.update_layout(
        title=(
            "Observed high cost rate "
            "by risk score band"
        )
    )

    figure.update_yaxes(
        title="Observed high cost event rate",
        tickformat=".0%",
        secondary_y=False
    )

    figure.update_yaxes(
        title="Historical records",
        secondary_y=True,
        showgrid=False
    )

    return apply_standard_layout(
        figure,
        height=450
    )


def model_metric_comparison_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "Model evaluation metrics"
        )

    prepared = dataframe.copy()

    preferred_metrics = [
        "Average precision",
        "Average precision lift",
        "ROC AUC",
        "Precision",
        "Recall",
        "F1",
        "F2",
        "Brier score"
    ]

    available_metrics = set(
        prepared[
            "metric_name"
        ].astype(str)
    )

    selected_metrics = [
        metric_name
        for metric_name in preferred_metrics
        if metric_name in available_metrics
    ]

    if selected_metrics:

        prepared = prepared.loc[
            prepared[
                "metric_name"
            ].isin(
                selected_metrics
            )
        ]

    figure = px.bar(
        prepared,
        x="metric_name",
        y="metric_value",
        color="evaluation_context",
        barmode="group",
        text_auto=".3f",
        color_discrete_sequence=[
            THEME["blue"],
            THEME["purple"],
            THEME["teal"]
        ]
    )

    figure.update_layout(
        title="Model evaluation metrics"
    )

    figure.update_xaxes(
        title=None,
        tickangle=-25
    )

    figure.update_yaxes(
        title="Metric value"
    )

    return apply_standard_layout(
        figure,
        height=500
    )


def etys_scenario_projection_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "ETYS projection by scenario and year"
        )

    prepared = dataframe.copy()

    prepared[
        "projection_value"
    ] = pd.to_numeric(
        prepared[
            "projection_value"
        ],
        errors="coerce"
    )

    summary = (
        prepared
        .groupby(
            [
                "projection_year",
                "scenario_code"
            ],
            as_index=False
        )
        .agg(
            average_projection_value=(
                "projection_value",
                "mean"
            )
        )
    )

    figure = px.line(
        summary,
        x="projection_year",
        y="average_projection_value",
        color="scenario_code",
        markers=True,
        color_discrete_sequence=[
            THEME["purple"],
            THEME["teal"],
            THEME["amber"]
        ]
    )

    figure.update_layout(
        title="ETYS projection by scenario and year"
    )

    figure.update_xaxes(
        title="Projection year",
        dtick=2
    )

    figure.update_yaxes(
        title="Average projection value"
    )

    return apply_standard_layout(
        figure,
        height=470
    )


def etys_boundary_heatmap_figure(
    dataframe: pd.DataFrame,
    maximum_boundaries: int = 15
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "ETYS boundary projection heatmap"
        )

    prepared = dataframe.copy()

    prepared[
        "projection_value"
    ] = pd.to_numeric(
        prepared[
            "projection_value"
        ],
        errors="coerce"
    )

    boundary_ranking = (
        prepared
        .groupby(
            "etys_boundary_code"
        )[
            "projection_value"
        ]
        .apply(
            lambda values:
                values.abs().mean()
        )
        .sort_values(
            ascending=False
        )
        .head(
            maximum_boundaries
        )
        .index
    )

    filtered = prepared.loc[
        prepared[
            "etys_boundary_code"
        ].isin(
            boundary_ranking
        )
    ]

    pivot = filtered.pivot_table(
        index="etys_boundary_code",
        columns="projection_year",
        values="projection_value",
        aggfunc="median"
    )

    pivot = pivot.reindex(
        boundary_ranking
    )

    maximum_absolute_value = float(
        np.nanmax(
            np.abs(
                pivot.values
            )
        )
    )

    if not np.isfinite(
        maximum_absolute_value
    ) or maximum_absolute_value == 0:

        maximum_absolute_value = 1.0

    figure = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            zmin=-maximum_absolute_value,
            zmax=maximum_absolute_value,
            colorscale=[
                [0.00, "#2563EB"],
                [0.50, "#F8FAFC"],
                [1.00, "#DC2626"]
            ],
            colorbar={
                "title":
                    "Projection<br>value"
            },
            hovertemplate=(
                "Boundary: %{y}<br>"
                "Year: %{x}<br>"
                "Median projection: %{z:,.1f}"
                "<extra></extra>"
            )
        )
    )

    figure.update_layout(
        title="ETYS boundary projection heatmap"
    )

    figure.update_xaxes(
        title="Projection year"
    )

    figure.update_yaxes(
        title="ETYS boundary"
    )

    return apply_standard_layout(
        figure,
        height=570
    )


def etys_projection_range_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "Scenario projection range"
        )

    prepared = dataframe.copy()

    prepared[
        "projection_value"
    ] = pd.to_numeric(
        prepared[
            "projection_value"
        ],
        errors="coerce"
    )

    summary = (
        prepared
        .groupby(
            [
                "projection_year",
                "scenario_code"
            ]
        )[
            "projection_value"
        ]
        .agg(
            lower_quartile=lambda values:
                values.quantile(0.25),

            median="median",

            upper_quartile=lambda values:
                values.quantile(0.75)
        )
        .reset_index()
    )

    scenario_colours = [
        THEME["purple"],
        THEME["teal"],
        THEME["amber"]
    ]

    figure = go.Figure()

    for scenario_index, scenario_code in enumerate(
        sorted(
            summary[
                "scenario_code"
            ].dropna().astype(str).unique()
        )
    ):

        scenario_data = (
            summary.loc[
                summary[
                    "scenario_code"
                ].astype(str).eq(
                    scenario_code
                )
            ]
            .sort_values(
                "projection_year"
            )
        )

        colour = scenario_colours[
            scenario_index
            %
            len(scenario_colours)
        ]

        figure.add_trace(
            go.Scatter(
                x=scenario_data[
                    "projection_year"
                ],
                y=scenario_data[
                    "upper_quartile"
                ],
                mode="lines",
                line={
                    "width": 0,
                    "color": colour
                },
                showlegend=False,
                hoverinfo="skip"
            )
        )

        figure.add_trace(
            go.Scatter(
                x=scenario_data[
                    "projection_year"
                ],
                y=scenario_data[
                    "lower_quartile"
                ],
                mode="lines",
                line={
                    "width": 0,
                    "color": colour
                },
                fill="tonexty",
                fillcolor=(
                    "rgba(124, 58, 237, 0.10)"
                    if scenario_index == 0
                    else
                    "rgba(14, 116, 144, 0.10)"
                    if scenario_index == 1
                    else
                    "rgba(245, 158, 11, 0.10)"
                ),
                showlegend=False,
                hoverinfo="skip"
            )
        )

        figure.add_trace(
            go.Scatter(
                x=scenario_data[
                    "projection_year"
                ],
                y=scenario_data[
                    "median"
                ],
                mode="lines+markers",
                name=scenario_code,
                line={
                    "color": colour,
                    "width": 3
                },
                marker={
                    "size": 6
                },
                hovertemplate=(
                    f"Scenario: {scenario_code}<br>"
                    "Year: %{x}<br>"
                    "Median: %{y:,.1f}"
                    "<extra></extra>"
                )
            )
        )

    figure.update_layout(
        title="Scenario projection range"
    )

    figure.update_xaxes(
        title="Projection year",
        dtick=2
    )

    figure.update_yaxes(
        title="Projection value"
    )

    return apply_standard_layout(
        figure,
        height=470
    )


def data_quality_issue_summary_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "Recorded data quality issues"
        )

    category_candidates = [
        "issue_type",
        "issue_category",
        "issue_status",
        "source_dataframe_name"
    ]

    category_column = next(
        (
            column_name
            for column_name in category_candidates
            if column_name in dataframe.columns
        ),
        None
    )

    if category_column is None:

        return _empty_figure(
            "Recorded data quality issues",
            (
                "The data quality table is available, "
                "but no recognised category column was found."
            )
        )

    summary = (
        dataframe[
            category_column
        ]
        .fillna("Not specified")
        .astype(str)
        .value_counts()
        .rename_axis("quality_category")
        .reset_index(name="issue_count")
        .sort_values(
            "issue_count"
        )
    )

    figure = go.Figure(
        go.Bar(
            x=summary["issue_count"],
            y=summary["quality_category"],
            orientation="h",
            marker_color=THEME["amber"],
            text=summary["issue_count"],
            textposition="outside",
            hovertemplate=(
                "%{y}<br>"
                "Issues: %{x:,}"
                "<extra></extra>"
            )
        )
    )

    figure.update_layout(
        title="Recorded data quality issues"
    )

    figure.update_xaxes(
        title="Recorded issue count",
        dtick=1
    )

    figure.update_yaxes(
        title=None
    )

    return apply_standard_layout(
        figure,
        height=440
    )


def figure_catalogue() -> list[str]:

    return [
        "monthly_cost_exposure_figure",
        "cost_outcome_mix_figure",
        "daily_constraint_cost_figure",
        "cumulative_constraint_cost_figure",
        "exposure_calendar_heatmap_figure",
        "monthly_cost_ranking_figure",
        "financial_year_comparison_figure",
        "exceedance_cost_scatter_figure",
        "exposure_band_cost_boxplot_figure",
        "stress_correlation_heatmap_figure",
        "high_cost_rate_by_exposure_figure",
        "historical_risk_timeline_figure",
        "classification_confusion_matrix_figure",
        "score_band_event_rate_figure",
        "model_metric_comparison_figure",
        "etys_scenario_projection_figure",
        "etys_boundary_heatmap_figure",
        "etys_projection_range_figure",
        "data_quality_issue_summary_figure"
    ]

# STAGE_6C_4A_SCATTER_MISSING_SIZE_REPAIR

def exceedance_cost_scatter_figure(
    dataframe: pd.DataFrame
) -> go.Figure:

    if dataframe is None or dataframe.empty:

        return _empty_figure(
            "Forecast exceedance volume versus realised cost"
        )

    prepared = dataframe.copy()

    numeric_columns = [
        "total_exceedance_volume_mwh",
        "thermal_constraint_cost_gbp",
        "forecast_exceedance_groups",
        "maximum_single_period_exceedance_mw",
        "maximum_group_peak_utilisation_pct"
    ]

    for column_name in numeric_columns:

        if column_name in prepared.columns:

            prepared[column_name] = pd.to_numeric(
                prepared[column_name],
                errors="coerce"
            )

    prepared = prepared.dropna(
        subset=[
            "total_exceedance_volume_mwh",
            "thermal_constraint_cost_gbp"
        ]
    ).copy()

    if prepared.empty:

        return _empty_figure(
            "Forecast exceedance volume versus realised cost",
            (
                "No records contain both forecast exposure "
                "and realised thermal constraint cost."
            )
        )

    if "forecast_exceedance_groups" not in prepared.columns:

        prepared[
            "forecast_exceedance_groups"
        ] = 0.0

    prepared[
        "forecast_exceedance_groups"
    ] = (
        prepared[
            "forecast_exceedance_groups"
        ]
        .fillna(0)
        .clip(lower=0)
    )

    prepared[
        "scatter_marker_size"
    ] = (
        prepared[
            "forecast_exceedance_groups"
        ]
        +
        1.0
    )

    if "forecast_exposure_band" not in prepared.columns:

        prepared[
            "forecast_exposure_band"
        ] = "Not specified"

    prepared[
        "forecast_exposure_band"
    ] = (
        prepared[
            "forecast_exposure_band"
        ]
        .fillna("Not specified")
        .astype(str)
    )

    hover_configuration = {
        "settlement_date": True,
        "forecast_exceedance_groups": ":.0f",
        "maximum_single_period_exceedance_mw": ":,.0f",
        "maximum_group_peak_utilisation_pct": ":,.1f",
        "thermal_cost_band": True,
        "scatter_marker_size": False
    }

    hover_configuration = {
        column_name: display_setting
        for column_name, display_setting
        in hover_configuration.items()
        if column_name in prepared.columns
    }

    figure = px.scatter(
        prepared,
        x="total_exceedance_volume_mwh",
        y="thermal_constraint_cost_gbp",
        color="forecast_exposure_band",
        size="scatter_marker_size",
        size_max=20,
        hover_data=hover_configuration,
        color_discrete_map={
            **EXPOSURE_COLOUR_MAP,
            "Not specified": "#CBD5E1"
        },
        opacity=0.76
    )

    figure.update_traces(
        marker={
            "line": {
                "color": "#FFFFFF",
                "width": 0.7
            }
        }
    )

    figure.update_layout(
        title=(
            "Forecast exceedance volume "
            "versus realised cost"
        )
    )

    figure.update_xaxes(
        title="Forecast exposure, MWh equivalent"
    )

    figure.update_yaxes(
        title="Realised thermal constraint cost, GBP",
        tickprefix="£",
        separatethousands=True
    )

    return apply_standard_layout(
        figure,
        height=500
    )
