from __future__ import annotations

import os
from typing import Any, Iterable, Optional

import pandas as pd
from dash import Dash, Input, Output, ctx, dash_table, dcc, html
from flask import jsonify

import components
import database
import visuals


APP_TITLE = (
    "Great Britain Grid Congestion and Constraint "
    "Cost Intelligence Dashboard"
)

APP_SUBTITLE = (
    "An interactive decision support platform combining day ahead "
    "forecast congestion exposure, realised thermal constraint costs, "
    "historical machine learning evidence and Electricity Ten Year "
    "Statement planning context."
)

PAGE_IDS = [
    "executive_overview",
    "congestion_cost_trends",
    "stress_cost_relationship",
    "historical_ml_evidence",
    "etys_planning_context",
    "quality_governance",
]

PAGE_LABELS = {
    "executive_overview": "Executive Overview",
    "congestion_cost_trends": "Congestion and Cost",
    "stress_cost_relationship": "Stress and Cost",
    "historical_ml_evidence": "Historical Machine Learning",
    "etys_planning_context": "Electricity Ten Year Statement Context",
    "quality_governance": "Quality and Governance",
}

STARTUP_ERROR: Optional[str] = None


def empty_dataframe(columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
    return pd.DataFrame(columns=list(columns or []))


def safe_database_call(loader, fallback_columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
    global STARTUP_ERROR
    try:
        dataframe = loader()
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("The database loader did not return a pandas DataFrame.")
        return dataframe
    except Exception as database_error:
        STARTUP_ERROR = f"{type(database_error).__name__}: {database_error}"
        return empty_dataframe(fallback_columns)


def safe_filter_options() -> dict[str, Any]:
    options = {
        "daily": {
            "financial_years": [],
            "forecast_exposure_bands": [],
            "thermal_cost_bands": [],
        },
        "model": {
            "evaluation_contexts": [],
            "classification_results": [],
        },
        "etys": {
            "boundaries": [],
            "scenarios": [],
            "categories": [],
            "projection_years": [],
        },
    }
    try:
        options["daily"] = database.load_daily_filter_options()
    except Exception:
        pass
    try:
        options["model"] = database.load_model_filter_options()
    except Exception:
        pass
    try:
        options["etys"] = database.load_etys_filter_options()
    except Exception:
        pass
    return options


INITIAL_DATA = {
    "daily": safe_database_call(database.load_daily_core),
    "monthly": safe_database_call(database.load_monthly_trend),
    "stress": safe_database_call(database.load_stress_cost_relationship),
    "model_scores": safe_database_call(database.load_model_scores),
    "model_metrics": safe_database_call(database.load_model_metrics),
    "model_governance": safe_database_call(database.load_model_governance),
    "etys": safe_database_call(database.load_etys_context),
    "quality": safe_database_call(database.load_data_quality),
    "pipeline": safe_database_call(database.load_pipeline_status),
}

FILTER_OPTIONS = safe_filter_options()


def numeric_series(dataframe: pd.DataFrame, column_name: str) -> pd.Series:
    if column_name not in dataframe.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(dataframe[column_name], errors="coerce")


def date_series(dataframe: pd.DataFrame, column_name: str) -> pd.Series:
    if column_name not in dataframe.columns:
        return pd.Series(dtype="datetime64[ns]")
    return pd.to_datetime(dataframe[column_name], errors="coerce")


def aggregate_monthly(daily_dataframe: pd.DataFrame) -> pd.DataFrame:
    required_columns = {
        "settlement_date",
        "thermal_constraint_cost_gbp",
        "total_exceedance_volume_mwh",
    }
    if (
        daily_dataframe is None
        or daily_dataframe.empty
        or not required_columns.issubset(daily_dataframe.columns)
    ):
        return empty_dataframe(
            [
                "month_start_date",
                "calendar_year",
                "calendar_month",
                "calendar_month_name",
                "daily_record_count",
                "forecast_exceedance_day_count",
                "total_forecast_exceedance_groups",
                "total_exceedance_volume_mwh",
                "average_peak_utilisation_pct",
                "maximum_peak_utilisation_pct",
                "total_thermal_constraint_cost_gbp",
                "average_daily_thermal_constraint_cost_gbp",
                "maximum_daily_thermal_constraint_cost_gbp",
                "high_cost_day_count",
                "average_historical_risk_score",
            ]
        )

    prepared = daily_dataframe.copy()
    prepared["settlement_date"] = date_series(prepared, "settlement_date")
    prepared = prepared.dropna(subset=["settlement_date"])
    prepared["month_start_date"] = (
        prepared["settlement_date"].dt.to_period("M").dt.to_timestamp()
    )
    prepared["calendar_year"] = prepared["settlement_date"].dt.year
    prepared["calendar_month"] = prepared["settlement_date"].dt.month
    prepared["calendar_month_name"] = prepared["settlement_date"].dt.month_name()

    for column_name in [
        "thermal_constraint_cost_gbp",
        "total_exceedance_volume_mwh",
        "forecast_exceedance_groups",
        "maximum_group_peak_utilisation_pct",
        "high_cost_event_definition",
        "high_cost_risk_score",
    ]:
        if column_name not in prepared.columns:
            prepared[column_name] = 0.0
        prepared[column_name] = pd.to_numeric(prepared[column_name], errors="coerce")

    prepared["forecast_exceedance_day"] = (
        prepared["forecast_exceedance_groups"].fillna(0).gt(0).astype(int)
    )

    return (
        prepared.groupby("month_start_date", as_index=False)
        .agg(
            calendar_year=("calendar_year", "first"),
            calendar_month=("calendar_month", "first"),
            calendar_month_name=("calendar_month_name", "first"),
            daily_record_count=("settlement_date", "count"),
            forecast_exceedance_day_count=("forecast_exceedance_day", "sum"),
            total_forecast_exceedance_groups=("forecast_exceedance_groups", "sum"),
            total_exceedance_volume_mwh=("total_exceedance_volume_mwh", "sum"),
            average_peak_utilisation_pct=("maximum_group_peak_utilisation_pct", "mean"),
            maximum_peak_utilisation_pct=("maximum_group_peak_utilisation_pct", "max"),
            total_thermal_constraint_cost_gbp=("thermal_constraint_cost_gbp", "sum"),
            average_daily_thermal_constraint_cost_gbp=("thermal_constraint_cost_gbp", "mean"),
            maximum_daily_thermal_constraint_cost_gbp=("thermal_constraint_cost_gbp", "max"),
            high_cost_day_count=("high_cost_event_definition", "sum"),
            average_historical_risk_score=("high_cost_risk_score", "mean"),
        )
        .sort_values("month_start_date")
    )


def dataframe_table_payload(
    dataframe: pd.DataFrame,
    selected_columns: list[str],
    label_lookup: Optional[dict[str, str]] = None,
    maximum_rows: int = 200,
):
    label_lookup = label_lookup or {}
    if dataframe is None or dataframe.empty:
        return [], []

    available_columns = [
        column_name
        for column_name in selected_columns
        if column_name in dataframe.columns
    ]
    prepared = dataframe[available_columns].head(maximum_rows).copy()

    for column_name in prepared.columns:
        if pd.api.types.is_datetime64_any_dtype(prepared[column_name]):
            prepared[column_name] = prepared[column_name].dt.strftime("%d %b %Y")
        elif "date" in column_name.lower():
            parsed_dates = pd.to_datetime(prepared[column_name], errors="coerce")
            prepared[column_name] = parsed_dates.dt.strftime("%d %b %Y")

    columns = [
        {
            "name": label_lookup.get(
                column_name,
                column_name.replace("_", " ").title(),
            ),
            "id": column_name,
        }
        for column_name in available_columns
    ]
    return prepared.to_dict("records"), columns


def dashboard_table(table_id: str, data, columns):
    return dash_table.DataTable(
        id=table_id,
        data=data,
        columns=columns,
        page_size=15,
        sort_action="native",
        filter_action="native",
        export_format="csv",
        style_as_list_view=True,
        style_table={"overflowX": "auto", "borderRadius": "14px"},
        style_header={
            "backgroundColor": "#081A2D",
            "color": "#FFFFFF",
            "fontWeight": "700",
            "border": "0",
            "padding": "12px",
        },
        style_cell={
            "fontFamily": "Inter, Segoe UI, Arial, sans-serif",
            "fontSize": "12px",
            "color": "#172033",
            "backgroundColor": "#FFFFFF",
            "borderBottom": "1px solid #EEF2F6",
            "borderLeft": "0",
            "borderRight": "0",
            "padding": "11px",
            "textAlign": "left",
            "minWidth": "110px",
            "maxWidth": "250px",
            "whiteSpace": "normal",
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#F8FAFC",
            }
        ],
    )


def build_executive_kpis(
    daily_dataframe: pd.DataFrame,
    pipeline_dataframe: pd.DataFrame,
):
    if daily_dataframe is None:
        daily_dataframe = empty_dataframe()

    total_cost = numeric_series(
        daily_dataframe,
        "thermal_constraint_cost_gbp",
    ).sum(min_count=1)
    settlement_dates = date_series(daily_dataframe, "settlement_date")
    latest_date = settlement_dates.max() if not settlement_dates.empty else None
    exceedance_groups = numeric_series(daily_dataframe, "forecast_exceedance_groups")
    high_cost_events = numeric_series(daily_dataframe, "high_cost_event_definition")
    exceedance_volume = numeric_series(daily_dataframe, "total_exceedance_volume_mwh")
    maximum_period_exceedance = numeric_series(
        daily_dataframe,
        "maximum_single_period_exceedance_mw",
    )
    risk_scores = numeric_series(daily_dataframe, "high_cost_risk_score")

    quality_issue_count = None
    if (
        pipeline_dataframe is not None
        and not pipeline_dataframe.empty
        and "current_recorded_data_quality_issue_count" in pipeline_dataframe.columns
    ):
        quality_issue_count = pipeline_dataframe.iloc[0][
            "current_recorded_data_quality_issue_count"
        ]

    return [
        components.metric_card(
            title="Total thermal constraint cost",
            value=components.format_currency(total_cost),
            subtitle="Realised thermal constraint cost within the selected period.",
            icon="£",
            tone="teal",
        ),
        components.metric_card(
            title="Latest available date",
            value=components.format_date(latest_date),
            subtitle="Most recent integrated daily record within the current filters.",
            icon="◷",
            tone="blue",
        ),
        components.metric_card(
            title="Forecast exceedance days",
            value=components.format_integer(exceedance_groups.fillna(0).gt(0).sum()),
            subtitle="Days containing at least one forecast limit exceedance group.",
            icon="△",
            tone="amber",
        ),
        components.metric_card(
            title="High cost days",
            value=components.format_integer(high_cost_events.fillna(0).sum()),
            subtitle="Days exceeding the fixed high thermal constraint cost threshold.",
            icon="!",
            tone="red",
        ),
        components.metric_card(
            title="Forecast exceedance volume",
            value=(
                f"{components.format_compact_number(exceedance_volume.sum(min_count=1))} MWh"
            ),
            subtitle="MWh equivalent forecast exposure, not realised constrained energy.",
            icon="∑",
            tone="purple",
        ),
        components.metric_card(
            title="Peak period exceedance",
            value=(
                f"{components.format_compact_number(maximum_period_exceedance.max())} MW"
            ),
            subtitle="Largest single settlement period forecast limit exceedance.",
            icon="↗",
            tone="amber",
        ),
        components.metric_card(
            title="Historically scored days",
            value=components.format_integer(risk_scores.notna().sum()),
            subtitle="Days containing stored research classifier risk scores.",
            icon="◎",
            tone="blue",
        ),
        components.metric_card(
            title="Recorded quality issues",
            value=components.format_integer(quality_issue_count),
            subtitle="Formally recorded issues retained in the production data mart.",
            icon="✓",
            tone="green",
        ),
    ]


def build_latest_insight(daily_dataframe: pd.DataFrame):
    if (
        daily_dataframe is None
        or daily_dataframe.empty
        or "settlement_date" not in daily_dataframe.columns
    ):
        return components.empty_state(
            "No latest record available",
            "The selected filters do not contain an integrated daily record.",
        )

    prepared = daily_dataframe.copy()
    prepared["settlement_date"] = date_series(prepared, "settlement_date")
    prepared = prepared.sort_values("settlement_date")
    latest = prepared.iloc[-1]

    latest_date = components.format_date(latest.get("settlement_date"))
    cost = components.format_currency(latest.get("thermal_constraint_cost_gbp"))
    exposure_band = components.safe_scalar(
        latest.get("forecast_exposure_band"),
        "Not classified",
    )
    exceedance_volume = components.format_compact_number(
        latest.get("total_exceedance_volume_mwh")
    )
    risk_score = components.safe_scalar(latest.get("high_cost_risk_score"))
    risk_text = (
        f"{float(risk_score):.3f}"
        if risk_score is not None
        else "Not available for this date"
    )

    return html.Div(
        [
            components.insight_card(
                title="Latest cost position",
                body=(
                    f"The latest filtered record is {latest_date}, with realised "
                    f"thermal constraint cost of {cost}."
                ),
                recommendation=(
                    "Compare the latest value with the monthly trend before drawing "
                    "a wider conclusion."
                ),
                tone="information",
                icon="£",
            ),
            components.insight_card(
                title="Latest forecast exposure",
                body=(
                    f"The latest analytical exposure band is {exposure_band}, with "
                    f"approximately {exceedance_volume} MWh equivalent forecast exposure."
                ),
                recommendation=(
                    "Treat this as day ahead forecast exposure, not confirmed physical overload."
                ),
                tone="warning",
                icon="△",
            ),
            components.insight_card(
                title="Historical model evidence",
                body=f"The stored high thermal constraint cost risk score is {risk_text}.",
                recommendation=(
                    "The score is an uncalibrated empirical ranking and is not approved "
                    "for operational alerting."
                ),
                tone="planning",
                icon="◎",
            ),
        ],
        className="three-column-grid",
    )


def build_pipeline_cards(
    pipeline_dataframe: pd.DataFrame,
    quality_dataframe: pd.DataFrame,
):
    pipeline_row = (
        pipeline_dataframe.iloc[0]
        if pipeline_dataframe is not None and not pipeline_dataframe.empty
        else pd.Series(dtype="object")
    )
    return [
        components.metric_card(
            title="Integrated daily records",
            value=components.format_integer(
                pipeline_row.get("current_integrated_daily_record_count")
            ),
            subtitle="Daily cost and forecast stress records available through Azure SQL.",
            icon="▦",
            tone="teal",
        ),
        components.metric_card(
            title="Historical model scores",
            value=components.format_integer(
                pipeline_row.get("current_historical_model_score_record_count")
            ),
            subtitle="Stored historical classifier evaluation records.",
            icon="◎",
            tone="blue",
        ),
        components.metric_card(
            title="Electricity Ten Year Statement projections",
            value=components.format_integer(
                pipeline_row.get("current_etys_projection_record_count")
            ),
            subtitle="Long term boundary and scenario projection records.",
            icon="◇",
            tone="purple",
        ),
        components.metric_card(
            title="Data quality issues",
            value=components.format_integer(
                len(quality_dataframe) if quality_dataframe is not None else None
            ),
            subtitle="Recorded issues retained for transparent stakeholder review.",
            icon="✓",
            tone="amber",
        ),
    ]


def build_etys_cards(etys_dataframe: pd.DataFrame):
    if etys_dataframe is None:
        etys_dataframe = empty_dataframe()

    boundary_count = (
        etys_dataframe["etys_boundary_code"].nunique()
        if "etys_boundary_code" in etys_dataframe.columns
        else 0
    )
    scenario_count = (
        etys_dataframe["scenario_code"].nunique()
        if "scenario_code" in etys_dataframe.columns
        else 0
    )
    year_count = (
        etys_dataframe["projection_year"].nunique()
        if "projection_year" in etys_dataframe.columns
        else 0
    )

    return [
        components.metric_card(
            title="Electricity Ten Year Statement boundaries",
            value=components.format_integer(boundary_count),
            subtitle="Boundaries represented within the selected planning context.",
            icon="◇",
            tone="purple",
        ),
        components.metric_card(
            title="Planning scenarios",
            value=components.format_integer(scenario_count),
            subtitle="Long term scenarios represented within the selected data.",
            icon="≋",
            tone="teal",
        ),
        components.metric_card(
            title="Projection years",
            value=components.format_integer(year_count),
            subtitle="Distinct planning years available within the selected range.",
            icon="◷",
            tone="blue",
        ),
        components.metric_card(
            title="Projection records",
            value=components.format_integer(len(etys_dataframe)),
            subtitle="Quality passed planning context records displayed.",
            icon="▦",
            tone="green",
        ),
    ]


def build_governance_panel(governance_dataframe: pd.DataFrame):
    if governance_dataframe is None or governance_dataframe.empty:
        return components.empty_state(
            "Governance evidence unavailable",
            "The model governance view did not return any records.",
        )

    cards = []
    for _, row in governance_dataframe.iterrows():
        operational_value = row.get("operational_alerting_permitted", False)
        operational_permitted = False if pd.isna(operational_value) else bool(operational_value)
        tone = "success" if operational_permitted else "critical"
        cards.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.H3(
                                components.safe_scalar(row.get("model_name"), "Model"),
                                className="governance-card-title",
                            ),
                            components.status_pill(
                                components.safe_scalar(
                                    row.get("dashboard_status"),
                                    "Status unavailable",
                                ),
                                tone,
                            ),
                        ],
                        className="metric-card-top",
                    ),
                    html.P(
                        components.safe_scalar(
                            row.get("formal_deployment_decision"),
                            "Deployment decision unavailable.",
                        ),
                        className="governance-card-text",
                    ),
                    html.P(
                        components.safe_scalar(
                            row.get("important_limitation"),
                            "Limitation text unavailable.",
                        ),
                        className="governance-card-text",
                    ),
                ],
                className="governance-card",
            )
        )
    return html.Div(cards, className="equal-column-grid")


def dropdown_options(values: Iterable[Any]):
    return [{"label": str(value), "value": value} for value in values]


daily_dates = date_series(INITIAL_DATA["daily"], "settlement_date")
initial_minimum_date = daily_dates.min().date() if not daily_dates.dropna().empty else None
initial_maximum_date = daily_dates.max().date() if not daily_dates.dropna().empty else None

etys_year_values = FILTER_OPTIONS["etys"].get("projection_years", [])
etys_minimum_year = min(etys_year_values) if etys_year_values else 2025
etys_maximum_year = max(etys_year_values) if etys_year_values else 2045
etys_year_marks = {
    int(year_value): str(year_value)
    for year_value in etys_year_values
    if (
        year_value == etys_minimum_year
        or year_value == etys_maximum_year
        or (year_value - etys_minimum_year) % 5 == 0
    )
}


def operational_filter_panel():
    return html.Div(
        [
            html.Div(
                [
                    components.filter_group(
                        "Date range",
                        dcc.DatePickerRange(
                            id="operational-date-filter",
                            min_date_allowed=initial_minimum_date,
                            max_date_allowed=initial_maximum_date,
                            start_date=initial_minimum_date,
                            end_date=initial_maximum_date,
                            display_format="DD MMM YYYY",
                            clearable=True,
                        ),
                        "Filters daily congestion and thermal cost evidence.",
                    ),
                    components.filter_group(
                        "Financial year",
                        dcc.Dropdown(
                            id="financial-year-filter",
                            options=dropdown_options(
                                FILTER_OPTIONS["daily"].get("financial_years", [])
                            ),
                            value=[],
                            multi=True,
                            placeholder="All financial years",
                        ),
                    ),
                    components.filter_group(
                        "Forecast exposure band",
                        dcc.Dropdown(
                            id="exposure-band-filter",
                            options=dropdown_options(
                                FILTER_OPTIONS["daily"].get(
                                    "forecast_exposure_bands",
                                    [],
                                )
                            ),
                            value=[],
                            multi=True,
                            placeholder="All exposure bands",
                        ),
                    ),
                    components.filter_group(
                        "Thermal cost outcome",
                        dcc.Dropdown(
                            id="cost-band-filter",
                            options=dropdown_options(
                                FILTER_OPTIONS["daily"].get("thermal_cost_bands", [])
                            ),
                            value=[],
                            multi=True,
                            placeholder="All cost outcomes",
                        ),
                    ),
                ],
                className="filter-grid",
            ),
            html.Div(
                [
                    html.Button(
                        "Refresh Azure SQL data",
                        id="refresh-dashboard-button",
                        n_clicks=0,
                        className="refresh-button",
                    ),
                    html.Div(
                        "Filters query approved Azure SQL dashboard views only.",
                        className="filter-refresh-note",
                    ),
                ],
                className="filter-refresh-row",
            ),
        ],
        id="operational-filter-panel",
        className="filter-panel",
    )


def platform_information_strip():
    return html.Div(
        [
            html.Div(
                [
                    html.Div("Data platform", className="platform-information-label"),
                    html.Div("Azure SQL Database", className="platform-information-value"),
                ],
                className="platform-information-item",
            ),
            html.Div(
                [
                    html.Div("Application", className="platform-information-label"),
                    html.Div("Plotly Dash and Flask", className="platform-information-value"),
                ],
                className="platform-information-item",
            ),
            html.Div(
                [
                    html.Div("Deployment target", className="platform-information-label"),
                    html.Div("Azure App Service", className="platform-information-value"),
                ],
                className="platform-information-item",
            ),
            html.Div(
                [
                    html.Div("Platform purpose", className="platform-information-label"),
                    html.Div("Research and decision support", className="platform-information-value"),
                ],
                className="platform-information-item",
            ),
            html.Div(
                [
                    html.Div("What this dashboard does", className="platform-note-title"),
                    html.P(
                        (
                            "This dashboard helps stakeholders see how forecast congestion "
                            "pressure on Great Britain's electricity network relates to "
                            "realised thermal constraint costs. It combines day ahead exposure "
                            "indicators, historical cost patterns, model evidence and Electricity "
                            "Ten Year Statement planning projections so users can compare periods, "
                            "identify important events and review the evidence behind the results. "
                            "It supports research and planning, not live operational warning."
                        ),
                        className="platform-note-text",
                    ),
                    html.Div(
                        "Model development and dashboard created by Kamil Ridwan",
                        className="platform-credit",
                    ),
                ],
                className="platform-explanatory-note",
            ),
        ],
        className="platform-information-strip",
    )


initial_daily = INITIAL_DATA["daily"]
initial_monthly = aggregate_monthly(initial_daily) if not initial_daily.empty else INITIAL_DATA["monthly"]
initial_stress = INITIAL_DATA["stress"]
initial_model_scores = INITIAL_DATA["model_scores"]
initial_model_metrics = INITIAL_DATA["model_metrics"]
initial_etys = INITIAL_DATA["etys"]
initial_quality = INITIAL_DATA["quality"]
initial_pipeline = INITIAL_DATA["pipeline"]

daily_table_columns = [
    "settlement_date",
    "forecast_exposure_band",
    "forecast_exceedance_groups",
    "total_exceedance_volume_mwh",
    "maximum_single_period_exceedance_mw",
    "maximum_group_peak_utilisation_pct",
    "thermal_constraint_cost_gbp",
    "thermal_cost_band",
    "high_cost_risk_score",
    "classification_result",
]

daily_table_labels = {
    "settlement_date": "Settlement date",
    "forecast_exposure_band": "Forecast exposure",
    "forecast_exceedance_groups": "Exceedance groups",
    "total_exceedance_volume_mwh": "Exposure volume, MWh equivalent",
    "maximum_single_period_exceedance_mw": "Peak period exceedance, MW",
    "maximum_group_peak_utilisation_pct": "Peak utilisation, %",
    "thermal_constraint_cost_gbp": "Thermal cost, GBP",
    "thermal_cost_band": "Cost outcome",
    "high_cost_risk_score": "Historical risk score",
    "classification_result": "Classification outcome",
}

initial_daily_table_data, initial_daily_table_columns = dataframe_table_payload(
    (
        initial_daily.sort_values("settlement_date", ascending=False)
        if not initial_daily.empty and "settlement_date" in initial_daily.columns
        else initial_daily
    ),
    daily_table_columns,
    daily_table_labels,
)

quality_table_columns = [
    "issue_date",
    "source_dataframe_name",
    "issue_type",
    "issue_description",
    "issue_status",
    "resolution_note",
]
quality_table_labels = {
    "issue_date": "Issue date",
    "source_dataframe_name": "Source dataframe",
    "issue_type": "Issue type",
    "issue_description": "Description",
    "issue_status": "Status",
    "resolution_note": "Resolution note",
}
initial_quality_table_data, initial_quality_table_columns = dataframe_table_payload(
    initial_quality,
    quality_table_columns,
    quality_table_labels,
)


def executive_overview_page():
    return html.Main(
        [
            components.section_header(
                "EXECUTIVE INTELLIGENCE",
                "Grid congestion and constraint cost overview",
                (
                    "A stakeholder focused summary of forecast congestion exposure, "
                    "realised thermal constraint cost, historical model evidence and "
                    "data availability."
                ),
            ),
            components.methodology_notice(
                "Interpretation boundary",
                (
                    "Forecast limit exceedance is an analytical day ahead exposure measure. "
                    "It does not confirm physical overload."
                ),
                "information",
            ),
            html.Div(
                build_executive_kpis(initial_daily, initial_pipeline),
                id="executive-kpi-grid",
                className="metric-grid",
            ),
            html.Div(
                [
                    components.chart_card(
                        "overview-monthly-cost-exposure",
                        visuals.monthly_cost_exposure_figure(initial_monthly),
                    ),
                    components.chart_card(
                        "overview-cost-mix",
                        visuals.cost_outcome_mix_figure(initial_daily),
                    ),
                ],
                className="two-column-grid",
            ),
            html.Div(build_latest_insight(initial_daily), id="latest-insight-container"),
            components.explanation_panel(
                (
                    "A combined view of forecast limit exceedance, realised thermal cost "
                    "and historical model evidence."
                ),
                (
                    "It allows executives to understand the scale and direction of the "
                    "available constraint intelligence quickly."
                ),
                (
                    "Start with the KPI cards, then compare monthly cost with forecast "
                    "exposure and review the latest evidence narrative."
                ),
                (
                    "Investigate repeated cost peaks or sustained increases in forecast "
                    "exposure, while respecting the methodology notices."
                ),
            ),
        ],
        id="page-executive_overview",
        className="dashboard-page",
        style={"display": "flex"},
    )


def congestion_cost_page():
    return html.Main(
        [
            components.section_header(
                "HISTORICAL TREND ANALYSIS",
                "Congestion exposure and thermal cost trends",
                (
                    "Explore daily, monthly, seasonal and financial year behaviour across "
                    "the integrated analytical record."
                ),
            ),
            components.methodology_notice(
                "Forecast exceedance volume",
                (
                    "The displayed volume is MWh equivalent forecast exposure and is not "
                    "realised constrained energy."
                ),
                "warning",
            ),
            html.Div(
                [
                    components.chart_card(
                        "daily-cost-trend",
                        visuals.daily_constraint_cost_figure(initial_daily),
                    ),
                    components.chart_card(
                        "cumulative-cost-trend",
                        visuals.cumulative_constraint_cost_figure(initial_daily),
                    ),
                ],
                className="equal-column-grid",
            ),
            components.chart_card(
                "exposure-calendar",
                visuals.exposure_calendar_heatmap_figure(initial_daily),
            ),
            html.Div(
                [
                    components.chart_card(
                        "monthly-cost-ranking",
                        visuals.monthly_cost_ranking_figure(initial_monthly),
                    ),
                    components.chart_card(
                        "financial-year-comparison",
                        visuals.financial_year_comparison_figure(initial_daily),
                    ),
                ],
                className="equal-column-grid",
            ),
            html.Div(
                [
                    html.H3("Integrated daily evidence", className="chart-card-title"),
                    html.P(
                        "Detailed records behind the trend visuals. The table can be filtered, sorted and exported.",
                        className="chart-card-description",
                    ),
                    dashboard_table(
                        "daily-evidence-table",
                        initial_daily_table_data,
                        initial_daily_table_columns,
                    ),
                ],
                className="data-table-card",
            ),
        ],
        id="page-congestion_cost_trends",
        className="dashboard-page",
        style={"display": "none"},
    )


def stress_cost_page():
    return html.Main(
        [
            components.section_header(
                "RELATIONSHIP INTELLIGENCE",
                "Forecast stress and realised cost relationship",
                (
                    "Examine historical association between forecast exposure indicators "
                    "and realised thermal constraint cost outcomes."
                ),
            ),
            components.methodology_notice(
                "Association is not causation",
                (
                    "The relationships displayed are historical analytical associations "
                    "and do not establish a causal mechanism."
                ),
                "warning",
            ),
            components.chart_card(
                "exceedance-cost-scatter",
                visuals.exceedance_cost_scatter_figure(initial_stress),
            ),
            html.Div(
                [
                    components.chart_card(
                        "exposure-band-boxplot",
                        visuals.exposure_band_cost_boxplot_figure(initial_stress),
                    ),
                    components.chart_card(
                        "high-cost-rate-exposure",
                        visuals.high_cost_rate_by_exposure_figure(initial_stress),
                    ),
                ],
                className="equal-column-grid",
            ),
            components.chart_card(
                "stress-correlation-heatmap",
                visuals.stress_correlation_heatmap_figure(initial_stress),
            ),
            components.explanation_panel(
                "A comparison of forecast exposure measures with realised thermal cost.",
                (
                    "It helps identify which indicators have historically moved most closely "
                    "with cost outcomes."
                ),
                (
                    "Use the scatter and box plot to inspect dispersion, then use the correlation "
                    "matrix for relative ranking."
                ),
                (
                    "Use findings to guide further analysis, not to claim a direct causal relationship."
                ),
            ),
        ],
        id="page-stress_cost_relationship",
        className="dashboard-page",
        style={"display": "none"},
    )


def historical_ml_page():
    return html.Main(
        [
            components.section_header(
                "MODEL EVIDENCE AND GOVERNANCE",
                "Historical high cost risk ranking evidence",
                (
                    "Review historical classifier scores, classification outcomes, evaluation "
                    "metrics and the formal deployment decision."
                ),
            ),
            components.methodology_notice(
                "Research score only",
                (
                    "The high thermal constraint cost risk score is an uncalibrated empirical "
                    "ranking. It is not a literal probability and is not approved for operational alerting."
                ),
                "critical",
            ),
            html.Div(
                [
                    components.filter_group(
                        "Evaluation context",
                        dcc.Dropdown(
                            id="model-context-filter",
                            options=dropdown_options(
                                FILTER_OPTIONS["model"].get("evaluation_contexts", [])
                            ),
                            value=[],
                            multi=True,
                            placeholder="All evaluation contexts",
                        ),
                    ),
                    components.filter_group(
                        "Classification outcome",
                        dcc.Dropdown(
                            id="classification-result-filter",
                            options=dropdown_options(
                                FILTER_OPTIONS["model"].get("classification_results", [])
                            ),
                            value=[],
                            multi=True,
                            placeholder="All outcomes",
                        ),
                    ),
                ],
                className="filter-panel filter-grid",
            ),
            components.chart_card(
                "historical-risk-timeline",
                visuals.historical_risk_timeline_figure(initial_model_scores),
            ),
            html.Div(
                [
                    components.chart_card(
                        "classification-confusion-matrix",
                        visuals.classification_confusion_matrix_figure(initial_model_scores),
                    ),
                    components.chart_card(
                        "score-band-event-rate",
                        visuals.score_band_event_rate_figure(initial_model_scores),
                    ),
                ],
                className="equal-column-grid",
            ),
            components.chart_card(
                "model-metric-comparison",
                visuals.model_metric_comparison_figure(initial_model_metrics),
            ),
            html.Div(
                build_governance_panel(INITIAL_DATA["model_governance"]),
                id="model-governance-panel",
            ),
        ],
        id="page-historical_ml_evidence",
        className="dashboard-page",
        style={"display": "none"},
    )


def etys_page():
    return html.Main(
        [
            components.section_header(
                "LONG TERM PLANNING CONTEXT",
                "Electricity Ten Year Statement boundary and scenario intelligence",
                (
                    "Explore long term boundary projections across scenarios, categories and "
                    "planning years as a separate strategic context."
                ),
            ),
            components.methodology_notice(
                "Separate planning context",
                (
                    "Electricity Ten Year Statement projections are not daily operational predictors. "
                    "No approved mapping exists between the daily operational groups and the planning boundaries."
                ),
                "planning",
            ),
            html.Div(
                [
                    components.filter_group(
                        "Electricity Ten Year Statement boundary",
                        dcc.Dropdown(
                            id="etys-boundary-filter",
                            options=dropdown_options(FILTER_OPTIONS["etys"].get("boundaries", [])),
                            value=[],
                            multi=True,
                            placeholder="All boundaries",
                        ),
                    ),
                    components.filter_group(
                        "Planning scenario",
                        dcc.Dropdown(
                            id="etys-scenario-filter",
                            options=dropdown_options(FILTER_OPTIONS["etys"].get("scenarios", [])),
                            value=[],
                            multi=True,
                            placeholder="All scenarios",
                        ),
                    ),
                    components.filter_group(
                        "Planning category",
                        dcc.Dropdown(
                            id="etys-category-filter",
                            options=dropdown_options(FILTER_OPTIONS["etys"].get("categories", [])),
                            value=[],
                            multi=True,
                            placeholder="All categories",
                        ),
                    ),
                    components.filter_group(
                        "Projection year range",
                        dcc.RangeSlider(
                            id="etys-year-filter",
                            min=etys_minimum_year,
                            max=etys_maximum_year,
                            value=[etys_minimum_year, etys_maximum_year],
                            marks=etys_year_marks,
                            step=1,
                            allowCross=False,
                        ),
                    ),
                ],
                className="filter-panel filter-grid",
            ),
            html.Div(build_etys_cards(initial_etys), id="etys-kpi-grid", className="metric-grid"),
            components.chart_card(
                "etys-scenario-projection",
                visuals.etys_scenario_projection_figure(initial_etys),
            ),
            html.Div(
                [
                    components.chart_card(
                        "etys-boundary-heatmap",
                        visuals.etys_boundary_heatmap_figure(initial_etys),
                    ),
                    components.chart_card(
                        "etys-projection-range",
                        visuals.etys_projection_range_figure(initial_etys),
                    ),
                ],
                className="equal-column-grid",
            ),
            components.explanation_panel(
                (
                    "Long term Electricity Ten Year Statement projections by boundary, scenario, "
                    "category and planning year."
                ),
                "They provide strategic context about how boundary conditions may evolve.",
                "Compare scenario direction, projection spread and boundary level patterns.",
                "Use the evidence for planning discussion only, not daily operational prediction.",
            ),
        ],
        id="page-etys_planning_context",
        className="dashboard-page",
        style={"display": "none"},
    )


def quality_page():
    return html.Main(
        [
            components.section_header(
                "TRUST, PROVENANCE AND PERMITTED USE",
                "Data quality and analytical governance",
                (
                    "Inspect cloud pipeline coverage, recorded data quality issues, model status "
                    "and the limitations governing stakeholder use."
                ),
            ),
            html.Div(
                build_pipeline_cards(initial_pipeline, initial_quality),
                id="pipeline-kpi-grid",
                className="metric-grid",
            ),
            components.chart_card(
                "data-quality-summary",
                visuals.data_quality_issue_summary_figure(initial_quality),
            ),
            html.Div(
                [
                    html.H3("Recorded data quality evidence", className="chart-card-title"),
                    html.P(
                        (
                            "Issues retained within the production data mart for transparent "
                            "review and traceability."
                        ),
                        className="chart-card-description",
                    ),
                    dashboard_table(
                        "data-quality-table",
                        initial_quality_table_data,
                        initial_quality_table_columns,
                    ),
                ],
                className="data-table-card",
            ),
            html.Div(
                [
                    components.methodology_notice(
                        "Forecast interpretation",
                        (
                            "Forecast limit exceedance represents day ahead exposure and not confirmed physical overload."
                        ),
                        "information",
                    ),
                    components.methodology_notice(
                        "Model use restriction",
                        (
                            "The classifier is retained as a research candidate and is not approved for production operational alerting."
                        ),
                        "critical",
                    ),
                    components.methodology_notice(
                        "Electricity Ten Year Statement interpretation",
                        (
                            "Electricity Ten Year Statement data remain long term planning context with no approved operational group mapping."
                        ),
                        "planning",
                    ),
                ],
                className="three-column-grid",
            ),
        ],
        id="page-quality_governance",
        className="dashboard-page",
        style={"display": "none"},
    )


app = Dash(
    __name__,
    title=APP_TITLE,
    suppress_callback_exceptions=True,
    update_title="Refreshing Azure SQL intelligence...",
)
server = app.server


@server.get("/health")
def health_endpoint():
    try:
        health_result = database.run_health_check()
        return jsonify(
            {
                "application": APP_TITLE,
                "status": "healthy",
                "database_connection": health_result.get("database_connection"),
                "database_name": health_result.get("database_name"),
                "approved_view_count": health_result.get("approved_view_count"),
                "operational_alerting_approved": False,
            }
        ), 200
    except Exception as health_error:
        return jsonify(
            {
                "application": APP_TITLE,
                "status": "unhealthy",
                "error": f"{type(health_error).__name__}: {health_error}",
            }
        ), 503


navigation_buttons = html.Div(
    [
        html.Button(
            PAGE_LABELS[page_id],
            id=f"nav-{page_id}",
            n_clicks=0,
            className=(
                "navigation-button active"
                if page_id == "executive_overview"
                else "navigation-button"
            ),
        )
        for page_id in PAGE_IDS
    ],
    className="page-navigation",
)

startup_notice = (
    components.methodology_notice(
        "Azure SQL connection warning",
        (
            "The application loaded without live database data. Check the App Service "
            f"environment settings. Technical detail: {STARTUP_ERROR}"
        ),
        "critical",
    )
    if STARTUP_ERROR
    else None
)

latest_date_text = (
    components.format_date(initial_maximum_date)
    if initial_maximum_date
    else "Latest date unavailable"
)

app.layout = html.Div(
    [
        html.Div(
            [
                components.hero_header(
                    title=APP_TITLE,
                    subtitle=APP_SUBTITLE,
                    pipeline_text="Azure SQL analytical views ready",
                    platform_text="Research and decision support",
                    latest_date_text=f"Latest data {latest_date_text}",
                ),
                platform_information_strip(),
                navigation_buttons,
                startup_notice,
                operational_filter_panel(),
                executive_overview_page(),
                congestion_cost_page(),
                stress_cost_page(),
                historical_ml_page(),
                etys_page(),
                quality_page(),
                html.Div(
                    (
                        "Research and decision support platform. Not an official operational alerting system."
                    ),
                    className="dashboard-footer-minimal",
                ),
            ],
            className="dashboard-content",
        )
    ],
    className="dashboard-shell",
)

navigation_outputs = [
    Output(f"page-{page_id}", "style") for page_id in PAGE_IDS
] + [
    Output(f"nav-{page_id}", "className") for page_id in PAGE_IDS
] + [
    Output("operational-filter-panel", "style")
]

navigation_inputs = [Input(f"nav-{page_id}", "n_clicks") for page_id in PAGE_IDS]


@app.callback(navigation_outputs, navigation_inputs)
def navigate_pages(*navigation_clicks):
    triggered_id = ctx.triggered_id
    if triggered_id is None or not str(triggered_id).startswith("nav-"):
        active_page = "executive_overview"
    else:
        active_page = str(triggered_id).replace("nav-", "", 1)

    page_styles = [
        {"display": "flex"} if page_id == active_page else {"display": "none"}
        for page_id in PAGE_IDS
    ]
    navigation_classes = [
        "navigation-button active" if page_id == active_page else "navigation-button"
        for page_id in PAGE_IDS
    ]
    operational_filter_style = (
        {"display": "block"}
        if active_page
        in {
            "executive_overview",
            "congestion_cost_trends",
            "stress_cost_relationship",
        }
        else {"display": "none"}
    )
    return page_styles + navigation_classes + [operational_filter_style]


@app.callback(
    Output("executive-kpi-grid", "children"),
    Output("overview-monthly-cost-exposure", "figure"),
    Output("overview-cost-mix", "figure"),
    Output("latest-insight-container", "children"),
    Output("daily-cost-trend", "figure"),
    Output("cumulative-cost-trend", "figure"),
    Output("exposure-calendar", "figure"),
    Output("monthly-cost-ranking", "figure"),
    Output("financial-year-comparison", "figure"),
    Output("exceedance-cost-scatter", "figure"),
    Output("exposure-band-boxplot", "figure"),
    Output("high-cost-rate-exposure", "figure"),
    Output("stress-correlation-heatmap", "figure"),
    Output("daily-evidence-table", "data"),
    Output("daily-evidence-table", "columns"),
    Input("operational-date-filter", "start_date"),
    Input("operational-date-filter", "end_date"),
    Input("financial-year-filter", "value"),
    Input("exposure-band-filter", "value"),
    Input("cost-band-filter", "value"),
    Input("refresh-dashboard-button", "n_clicks"),
)
def update_operational_intelligence(
    start_date,
    end_date,
    financial_years,
    exposure_bands,
    cost_bands,
    refresh_clicks,
):
    daily_dataframe = database.load_daily_core(
        start_date=start_date,
        end_date=end_date,
        financial_years=financial_years,
        forecast_exposure_bands=exposure_bands,
        thermal_cost_bands=cost_bands,
    )
    stress_dataframe = database.load_stress_cost_relationship(
        start_date=start_date,
        end_date=end_date,
        financial_years=financial_years,
        forecast_exposure_bands=exposure_bands,
        thermal_cost_bands=cost_bands,
    )
    pipeline_dataframe = database.load_pipeline_status()
    monthly_dataframe = aggregate_monthly(daily_dataframe)

    sorted_daily_dataframe = (
        daily_dataframe.sort_values("settlement_date", ascending=False)
        if not daily_dataframe.empty and "settlement_date" in daily_dataframe.columns
        else daily_dataframe
    )
    table_data, table_columns = dataframe_table_payload(
        sorted_daily_dataframe,
        daily_table_columns,
        daily_table_labels,
    )

    return (
        build_executive_kpis(daily_dataframe, pipeline_dataframe),
        visuals.monthly_cost_exposure_figure(monthly_dataframe),
        visuals.cost_outcome_mix_figure(daily_dataframe),
        build_latest_insight(daily_dataframe),
        visuals.daily_constraint_cost_figure(daily_dataframe),
        visuals.cumulative_constraint_cost_figure(daily_dataframe),
        visuals.exposure_calendar_heatmap_figure(daily_dataframe),
        visuals.monthly_cost_ranking_figure(monthly_dataframe),
        visuals.financial_year_comparison_figure(daily_dataframe),
        visuals.exceedance_cost_scatter_figure(stress_dataframe),
        visuals.exposure_band_cost_boxplot_figure(stress_dataframe),
        visuals.high_cost_rate_by_exposure_figure(stress_dataframe),
        visuals.stress_correlation_heatmap_figure(stress_dataframe),
        table_data,
        table_columns,
    )


@app.callback(
    Output("historical-risk-timeline", "figure"),
    Output("classification-confusion-matrix", "figure"),
    Output("score-band-event-rate", "figure"),
    Output("model-metric-comparison", "figure"),
    Output("model-governance-panel", "children"),
    Input("model-context-filter", "value"),
    Input("classification-result-filter", "value"),
)
def update_model_evidence(evaluation_contexts, classification_results):
    model_scores_dataframe = database.load_model_scores(
        evaluation_contexts=evaluation_contexts,
        classification_results=classification_results,
    )
    model_metrics_dataframe = database.load_model_metrics(
        evaluation_contexts=evaluation_contexts
    )
    governance_dataframe = database.load_model_governance()
    return (
        visuals.historical_risk_timeline_figure(model_scores_dataframe),
        visuals.classification_confusion_matrix_figure(model_scores_dataframe),
        visuals.score_band_event_rate_figure(model_scores_dataframe),
        visuals.model_metric_comparison_figure(model_metrics_dataframe),
        build_governance_panel(governance_dataframe),
    )


@app.callback(
    Output("etys-kpi-grid", "children"),
    Output("etys-scenario-projection", "figure"),
    Output("etys-boundary-heatmap", "figure"),
    Output("etys-projection-range", "figure"),
    Input("etys-boundary-filter", "value"),
    Input("etys-scenario-filter", "value"),
    Input("etys-category-filter", "value"),
    Input("etys-year-filter", "value"),
)
def update_etys_context(boundaries, scenarios, categories, year_range):
    year_range = year_range or [etys_minimum_year, etys_maximum_year]
    etys_dataframe = database.load_etys_context(
        boundaries=boundaries,
        scenarios=scenarios,
        categories=categories,
        projection_year_start=year_range[0],
        projection_year_end=year_range[1],
    )
    return (
        build_etys_cards(etys_dataframe),
        visuals.etys_scenario_projection_figure(etys_dataframe),
        visuals.etys_boundary_heatmap_figure(etys_dataframe),
        visuals.etys_projection_range_figure(etys_dataframe),
    )


@app.callback(
    Output("pipeline-kpi-grid", "children"),
    Output("data-quality-summary", "figure"),
    Output("data-quality-table", "data"),
    Output("data-quality-table", "columns"),
    Input("refresh-dashboard-button", "n_clicks"),
)
def update_quality_governance(refresh_clicks):
    pipeline_dataframe = database.load_pipeline_status()
    quality_dataframe = database.load_data_quality()
    table_data, table_columns = dataframe_table_payload(
        quality_dataframe,
        quality_table_columns,
        quality_table_labels,
    )
    return (
        build_pipeline_cards(pipeline_dataframe, quality_dataframe),
        visuals.data_quality_issue_summary_figure(quality_dataframe),
        table_data,
        table_columns,
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8050")),
        debug=False,
    )
