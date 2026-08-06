from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Iterable, Optional
from urllib.parse import quote_plus

import pandas as pd

from sqlalchemy import bindparam
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.engine import Engine


APPROVED_DASHBOARD_VIEWS = {
    "vw_dashboard_daily_core",
    "vw_dashboard_latest_position",
    "vw_dashboard_kpi_summary",
    "vw_dashboard_monthly_trend",
    "vw_dashboard_stress_cost_relationship",
    "vw_dashboard_model_scores",
    "vw_dashboard_model_governance",
    "vw_dashboard_model_metrics",
    "vw_dashboard_etys_context",
    "vw_dashboard_data_quality",
    "vw_dashboard_pipeline_status"
}


def _required_environment_value(
    variable_name: str
) -> str:

    value = os.getenv(variable_name)

    if value is None or not value.strip():

        raise RuntimeError(
            f"Required environment variable "
            f"{variable_name} is not configured."
        )

    return value.strip()


def _build_odbc_connection_string() -> str:

    supplied_connection_string = os.getenv(
        "AZURE_SQL_ODBC_CONNECTION_STRING"
    )

    if (
        supplied_connection_string is not None
        and supplied_connection_string.strip()
    ):

        return supplied_connection_string.strip()

    server = _required_environment_value(
        "AZURE_SQL_SERVER"
    )

    database = _required_environment_value(
        "AZURE_SQL_DATABASE"
    )

    username = _required_environment_value(
        "AZURE_SQL_USERNAME"
    )

    password = _required_environment_value(
        "AZURE_SQL_PASSWORD"
    )

    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER=tcp:{server},1433;"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=60;"
        "ApplicationIntent=ReadOnly;"
    )


@lru_cache(maxsize=1)
def get_engine() -> Engine:

    odbc_connection_string = (
        _build_odbc_connection_string()
    )

    encoded_connection_string = quote_plus(
        odbc_connection_string
    )

    return create_engine(
        (
            "mssql+pyodbc:///?odbc_connect="
            f"{encoded_connection_string}"
        ),
        pool_pre_ping=True,
        pool_recycle=1800,
        future=True
    )


def dispose_engine() -> None:

    if get_engine.cache_info().currsize:

        get_engine().dispose()
        get_engine.cache_clear()


def _resolve_engine(
    engine: Optional[Engine]
) -> Engine:

    return (
        engine
        if engine is not None
        else get_engine()
    )


def _normalise_values(
    values: Optional[Iterable[Any]]
) -> list[Any]:

    if values is None:

        return []

    if isinstance(
        values,
        (
            str,
            bytes
        )
    ):

        values = [values]

    normalised_values = []

    for value in values:

        if value is None:

            continue

        if isinstance(value, str):

            value = value.strip()

            if not value:

                continue

        if value not in normalised_values:

            normalised_values.append(
                value
            )

    return normalised_values


def _execute_dataframe_query(
    sql_text: str,
    parameters: Optional[dict[str, Any]] = None,
    expanding_parameters: Optional[list[str]] = None,
    engine: Optional[Engine] = None
) -> pd.DataFrame:

    parameters = parameters or {}
    expanding_parameters = (
        expanding_parameters
        or
        []
    )

    sql_statement = text(
        sql_text
    )

    for parameter_name in expanding_parameters:

        sql_statement = sql_statement.bindparams(
            bindparam(
                parameter_name,
                expanding=True
            )
        )

    resolved_engine = _resolve_engine(
        engine
    )

    with resolved_engine.connect() as connection:

        dataframe = pd.read_sql(
            sql_statement,
            connection,
            params=parameters
        )

    return dataframe


def _validate_approved_view(
    view_name: str
) -> None:

    if view_name not in APPROVED_DASHBOARD_VIEWS:

        raise ValueError(
            f"View {view_name} is not approved "
            "for dashboard access."
        )


def load_approved_view(
    view_name: str,
    engine: Optional[Engine] = None
) -> pd.DataFrame:

    _validate_approved_view(
        view_name
    )

    return _execute_dataframe_query(
        sql_text=(
            f"SELECT * "
            f"FROM analytics.[{view_name}]"
        ),
        engine=engine
    )


def load_latest_position(
    engine: Optional[Engine] = None
) -> pd.DataFrame:

    return _execute_dataframe_query(
        sql_text="""
        SELECT *
        FROM analytics.vw_dashboard_latest_position
        """,
        engine=engine
    )


def load_kpi_summary(
    engine: Optional[Engine] = None
) -> pd.DataFrame:

    return _execute_dataframe_query(
        sql_text="""
        SELECT *
        FROM analytics.vw_dashboard_kpi_summary
        """,
        engine=engine
    )


def load_monthly_trend(
    engine: Optional[Engine] = None
) -> pd.DataFrame:

    return _execute_dataframe_query(
        sql_text="""
        SELECT *
        FROM analytics.vw_dashboard_monthly_trend
        ORDER BY month_start_date
        """,
        engine=engine
    )


def load_daily_core(
    start_date: Optional[Any] = None,
    end_date: Optional[Any] = None,
    financial_years: Optional[Iterable[str]] = None,
    forecast_exposure_bands: Optional[Iterable[str]] = None,
    thermal_cost_bands: Optional[Iterable[str]] = None,
    engine: Optional[Engine] = None
) -> pd.DataFrame:

    where_clauses = [
        "1 = 1"
    ]

    parameters: dict[str, Any] = {}

    expanding_parameters: list[str] = []

    if start_date is not None:

        where_clauses.append(
            "settlement_date >= :start_date"
        )

        parameters[
            "start_date"
        ] = pd.Timestamp(
            start_date
        ).date()

    if end_date is not None:

        where_clauses.append(
            "settlement_date <= :end_date"
        )

        parameters[
            "end_date"
        ] = pd.Timestamp(
            end_date
        ).date()

    financial_year_values = _normalise_values(
        financial_years
    )

    if financial_year_values:

        where_clauses.append(
            "financial_year IN :financial_years"
        )

        parameters[
            "financial_years"
        ] = financial_year_values

        expanding_parameters.append(
            "financial_years"
        )

    exposure_band_values = _normalise_values(
        forecast_exposure_bands
    )

    if exposure_band_values:

        where_clauses.append(
            (
                "forecast_exposure_band "
                "IN :forecast_exposure_bands"
            )
        )

        parameters[
            "forecast_exposure_bands"
        ] = exposure_band_values

        expanding_parameters.append(
            "forecast_exposure_bands"
        )

    cost_band_values = _normalise_values(
        thermal_cost_bands
    )

    if cost_band_values:

        where_clauses.append(
            (
                "thermal_cost_band "
                "IN :thermal_cost_bands"
            )
        )

        parameters[
            "thermal_cost_bands"
        ] = cost_band_values

        expanding_parameters.append(
            "thermal_cost_bands"
        )

    sql_text = f"""
        SELECT *
        FROM analytics.vw_dashboard_daily_core
        WHERE {' AND '.join(where_clauses)}
        ORDER BY settlement_date
    """

    return _execute_dataframe_query(
        sql_text=sql_text,
        parameters=parameters,
        expanding_parameters=expanding_parameters,
        engine=engine
    )


def load_stress_cost_relationship(
    start_date: Optional[Any] = None,
    end_date: Optional[Any] = None,
    financial_years: Optional[Iterable[str]] = None,
    forecast_exposure_bands: Optional[Iterable[str]] = None,
    thermal_cost_bands: Optional[Iterable[str]] = None,
    engine: Optional[Engine] = None
) -> pd.DataFrame:

    where_clauses = [
        "1 = 1"
    ]

    parameters: dict[str, Any] = {}

    expanding_parameters: list[str] = []

    if start_date is not None:

        where_clauses.append(
            "settlement_date >= :start_date"
        )

        parameters[
            "start_date"
        ] = pd.Timestamp(
            start_date
        ).date()

    if end_date is not None:

        where_clauses.append(
            "settlement_date <= :end_date"
        )

        parameters[
            "end_date"
        ] = pd.Timestamp(
            end_date
        ).date()

    financial_year_values = _normalise_values(
        financial_years
    )

    if financial_year_values:

        where_clauses.append(
            "financial_year IN :financial_years"
        )

        parameters[
            "financial_years"
        ] = financial_year_values

        expanding_parameters.append(
            "financial_years"
        )

    exposure_band_values = _normalise_values(
        forecast_exposure_bands
    )

    if exposure_band_values:

        where_clauses.append(
            (
                "forecast_exposure_band "
                "IN :forecast_exposure_bands"
            )
        )

        parameters[
            "forecast_exposure_bands"
        ] = exposure_band_values

        expanding_parameters.append(
            "forecast_exposure_bands"
        )

    cost_band_values = _normalise_values(
        thermal_cost_bands
    )

    if cost_band_values:

        where_clauses.append(
            (
                "thermal_cost_band "
                "IN :thermal_cost_bands"
            )
        )

        parameters[
            "thermal_cost_bands"
        ] = cost_band_values

        expanding_parameters.append(
            "thermal_cost_bands"
        )

    sql_text = f"""
        SELECT *
        FROM analytics.vw_dashboard_stress_cost_relationship
        WHERE {' AND '.join(where_clauses)}
        ORDER BY settlement_date
    """

    return _execute_dataframe_query(
        sql_text=sql_text,
        parameters=parameters,
        expanding_parameters=expanding_parameters,
        engine=engine
    )


def load_model_scores(
    evaluation_contexts: Optional[Iterable[str]] = None,
    classification_results: Optional[Iterable[str]] = None,
    engine: Optional[Engine] = None
) -> pd.DataFrame:

    where_clauses = [
        "1 = 1"
    ]

    parameters: dict[str, Any] = {}

    expanding_parameters: list[str] = []

    evaluation_context_values = _normalise_values(
        evaluation_contexts
    )

    if evaluation_context_values:

        where_clauses.append(
            (
                "evaluation_context "
                "IN :evaluation_contexts"
            )
        )

        parameters[
            "evaluation_contexts"
        ] = evaluation_context_values

        expanding_parameters.append(
            "evaluation_contexts"
        )

    classification_result_values = _normalise_values(
        classification_results
    )

    if classification_result_values:

        where_clauses.append(
            (
                "classification_result "
                "IN :classification_results"
            )
        )

        parameters[
            "classification_results"
        ] = classification_result_values

        expanding_parameters.append(
            "classification_results"
        )

    sql_text = f"""
        SELECT *
        FROM analytics.vw_dashboard_model_scores
        WHERE {' AND '.join(where_clauses)}
        ORDER BY settlement_date
    """

    return _execute_dataframe_query(
        sql_text=sql_text,
        parameters=parameters,
        expanding_parameters=expanding_parameters,
        engine=engine
    )


def load_model_governance(
    engine: Optional[Engine] = None
) -> pd.DataFrame:

    return _execute_dataframe_query(
        sql_text="""
        SELECT *
        FROM analytics.vw_dashboard_model_governance
        ORDER BY model_key
        """,
        engine=engine
    )


def load_model_metrics(
    evaluation_contexts: Optional[Iterable[str]] = None,
    engine: Optional[Engine] = None
) -> pd.DataFrame:

    where_clauses = [
        "1 = 1"
    ]

    parameters: dict[str, Any] = {}

    expanding_parameters: list[str] = []

    evaluation_context_values = _normalise_values(
        evaluation_contexts
    )

    if evaluation_context_values:

        where_clauses.append(
            (
                "evaluation_context "
                "IN :evaluation_contexts"
            )
        )

        parameters[
            "evaluation_contexts"
        ] = evaluation_context_values

        expanding_parameters.append(
            "evaluation_contexts"
        )

    sql_text = f"""
        SELECT *
        FROM analytics.vw_dashboard_model_metrics
        WHERE {' AND '.join(where_clauses)}
        ORDER BY
            model_key,
            evaluation_context,
            metric_name
    """

    return _execute_dataframe_query(
        sql_text=sql_text,
        parameters=parameters,
        expanding_parameters=expanding_parameters,
        engine=engine
    )


def load_etys_context(
    boundaries: Optional[Iterable[str]] = None,
    scenarios: Optional[Iterable[str]] = None,
    categories: Optional[Iterable[str]] = None,
    projection_year_start: Optional[int] = None,
    projection_year_end: Optional[int] = None,
    engine: Optional[Engine] = None
) -> pd.DataFrame:

    where_clauses = [
        "1 = 1"
    ]

    parameters: dict[str, Any] = {}

    expanding_parameters: list[str] = []

    boundary_values = _normalise_values(
        boundaries
    )

    if boundary_values:

        where_clauses.append(
            "etys_boundary_code IN :boundaries"
        )

        parameters[
            "boundaries"
        ] = boundary_values

        expanding_parameters.append(
            "boundaries"
        )

    scenario_values = _normalise_values(
        scenarios
    )

    if scenario_values:

        where_clauses.append(
            "scenario_code IN :scenarios"
        )

        parameters[
            "scenarios"
        ] = scenario_values

        expanding_parameters.append(
            "scenarios"
        )

    category_values = _normalise_values(
        categories
    )

    if category_values:

        where_clauses.append(
            "category_code IN :categories"
        )

        parameters[
            "categories"
        ] = category_values

        expanding_parameters.append(
            "categories"
        )

    if projection_year_start is not None:

        where_clauses.append(
            (
                "projection_year "
                ">= :projection_year_start"
            )
        )

        parameters[
            "projection_year_start"
        ] = int(
            projection_year_start
        )

    if projection_year_end is not None:

        where_clauses.append(
            (
                "projection_year "
                "<= :projection_year_end"
            )
        )

        parameters[
            "projection_year_end"
        ] = int(
            projection_year_end
        )

    sql_text = f"""
        SELECT *
        FROM analytics.vw_dashboard_etys_context
        WHERE {' AND '.join(where_clauses)}
        ORDER BY
            etys_boundary_code,
            scenario_code,
            category_code,
            projection_year
    """

    return _execute_dataframe_query(
        sql_text=sql_text,
        parameters=parameters,
        expanding_parameters=expanding_parameters,
        engine=engine
    )


def load_data_quality(
    engine: Optional[Engine] = None
) -> pd.DataFrame:

    return _execute_dataframe_query(
        sql_text="""
        SELECT *
        FROM analytics.vw_dashboard_data_quality
        ORDER BY issue_date, source_dataframe_name
        """,
        engine=engine
    )


def load_pipeline_status(
    engine: Optional[Engine] = None
) -> pd.DataFrame:

    return _execute_dataframe_query(
        sql_text="""
        SELECT *
        FROM analytics.vw_dashboard_pipeline_status
        """,
        engine=engine
    )


def load_daily_filter_options(
    engine: Optional[Engine] = None
) -> dict[str, list[Any]]:

    dataframe = _execute_dataframe_query(
        sql_text="""
        SELECT DISTINCT
            financial_year,
            forecast_exposure_band,
            thermal_cost_band
        FROM analytics.vw_dashboard_daily_core
        """,
        engine=engine
    )

    return {
        "financial_years":
            sorted(
                dataframe[
                    "financial_year"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),

        "forecast_exposure_bands":
            sorted(
                dataframe[
                    "forecast_exposure_band"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),

        "thermal_cost_bands":
            sorted(
                dataframe[
                    "thermal_cost_band"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
    }


def load_model_filter_options(
    engine: Optional[Engine] = None
) -> dict[str, list[Any]]:

    dataframe = _execute_dataframe_query(
        sql_text="""
        SELECT DISTINCT
            evaluation_context,
            classification_result
        FROM analytics.vw_dashboard_model_scores
        """,
        engine=engine
    )

    return {
        "evaluation_contexts":
            sorted(
                dataframe[
                    "evaluation_context"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),

        "classification_results":
            sorted(
                dataframe[
                    "classification_result"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
    }


def load_etys_filter_options(
    engine: Optional[Engine] = None
) -> dict[str, list[Any]]:

    dataframe = _execute_dataframe_query(
        sql_text="""
        SELECT DISTINCT
            etys_boundary_code,
            scenario_code,
            category_code,
            projection_year
        FROM analytics.vw_dashboard_etys_context
        """,
        engine=engine
    )

    return {
        "boundaries":
            sorted(
                dataframe[
                    "etys_boundary_code"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),

        "scenarios":
            sorted(
                dataframe[
                    "scenario_code"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),

        "categories":
            sorted(
                dataframe[
                    "category_code"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),

        "projection_years":
            sorted(
                dataframe[
                    "projection_year"
                ]
                .dropna()
                .astype(int)
                .unique()
                .tolist()
            )
    }


def run_health_check(
    engine: Optional[Engine] = None
) -> dict[str, Any]:

    resolved_engine = _resolve_engine(
        engine
    )

    with resolved_engine.connect() as connection:

        connection.execute(
            text("SELECT 1")
        )

        database_name = connection.execute(
            text("SELECT DB_NAME()")
        ).scalar_one()

    pipeline_status = load_pipeline_status(
        engine=resolved_engine
    )

    return {
        "database_connection":
            "Passed",

        "database_name":
            database_name,

        "pipeline_status_rows":
            int(
                len(pipeline_status)
            ),

        "approved_view_count":
            int(
                len(APPROVED_DASHBOARD_VIEWS)
            )
    }
