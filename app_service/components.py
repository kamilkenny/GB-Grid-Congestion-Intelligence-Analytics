from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable, Optional

import numpy as np
import pandas as pd

from dash import dcc, html


def safe_scalar(
    value: Any,
    default: Any = None
) -> Any:

    if value is None:

        return default

    try:

        if pd.isna(value):

            return default

    except Exception:

        pass

    return value


def format_compact_number(
    value: Any,
    decimals: int = 1
) -> str:

    value = safe_scalar(
        value
    )

    if value is None:

        return "Not available"

    numeric_value = float(
        value
    )

    absolute_value = abs(
        numeric_value
    )

    if absolute_value >= 1_000_000_000:

        return (
            f"{numeric_value / 1_000_000_000:,.{decimals}f}bn"
        )

    if absolute_value >= 1_000_000:

        return (
            f"{numeric_value / 1_000_000:,.{decimals}f}m"
        )

    if absolute_value >= 1_000:

        return (
            f"{numeric_value / 1_000:,.{decimals}f}k"
        )

    if float(
        numeric_value
    ).is_integer():

        return f"{int(numeric_value):,}"

    return f"{numeric_value:,.{decimals}f}"


def format_currency(
    value: Any,
    decimals: int = 1
) -> str:

    formatted_value = format_compact_number(
        value,
        decimals=decimals
    )

    if formatted_value == "Not available":

        return formatted_value

    return f"£{formatted_value}"


def format_integer(
    value: Any
) -> str:

    value = safe_scalar(
        value
    )

    if value is None:

        return "Not available"

    return f"{int(round(float(value))):,}"


def format_date(
    value: Any
) -> str:

    value = safe_scalar(
        value
    )

    if value is None:

        return "Not available"

    parsed_value = pd.to_datetime(
        value,
        errors="coerce"
    )

    if pd.isna(
        parsed_value
    ):

        return str(value)

    return parsed_value.strftime(
        "%d %b %Y"
    )


def status_pill(
    text: str,
    tone: str = "information"
):

    tone_class = {
        "success": "status-pill success",
        "warning": "status-pill warning",
        "critical": "status-pill critical",
        "planning": "status-pill planning",
        "information": "status-pill information",
        "neutral": "status-pill neutral"
    }.get(
        tone,
        "status-pill information"
    )

    return html.Span(
        text,
        className=tone_class
    )


def metric_card(
    title: str,
    value: str,
    subtitle: str,
    icon: str = "◈",
    tone: str = "teal",
    badge_text: Optional[str] = None,
    badge_tone: str = "information"
):

    badge_component = (
        status_pill(
            badge_text,
            badge_tone
        )
        if badge_text
        else None
    )

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        icon,
                        className=(
                            f"metric-icon "
                            f"metric-icon-{tone}"
                        )
                    ),
                    badge_component
                ],
                className="metric-card-top"
            ),
            html.Div(
                title,
                className="metric-card-title"
            ),
            html.Div(
                value,
                className="metric-card-value"
            ),
            html.Div(
                subtitle,
                className="metric-card-subtitle"
            )
        ],
        className=(
            f"metric-card "
            f"metric-card-{tone}"
        )
    )


def section_header(
    eyebrow: str,
    title: str,
    description: str,
    action_component: Any = None
):

    children = [
        html.Div(
            [
                html.Div(
                    eyebrow,
                    className="section-eyebrow"
                ),
                html.H2(
                    title,
                    className="section-title"
                ),
                html.P(
                    description,
                    className="section-description"
                )
            ],
            className="section-header-copy"
        )
    ]

    if action_component is not None:

        children.append(
            html.Div(
                action_component,
                className="section-header-action"
            )
        )

    return html.Div(
        children,
        className="section-header"
    )


def chart_card(
    graph_id: str,
    figure,
    title: Optional[str] = None,
    description: Optional[str] = None,
    class_name: str = ""
):

    heading_children = []

    if title:

        heading_children.append(
            html.H3(
                title,
                className="chart-card-title"
            )
        )

    if description:

        heading_children.append(
            html.P(
                description,
                className="chart-card-description"
            )
        )

    return html.Div(
        [
            html.Div(
                heading_children,
                className="chart-card-heading"
            )
            if heading_children
            else None,

            dcc.Loading(
                dcc.Graph(
                    id=graph_id,
                    figure=figure,
                    config={
                        "displaylogo": False,
                        "responsive": True,
                        "modeBarButtonsToRemove": [
                            "lasso2d",
                            "select2d"
                        ]
                    },
                    className="dashboard-graph"
                ),
                type="circle",
                className="chart-loading"
            )
        ],
        className=(
            f"chart-card {class_name}"
        ).strip()
    )


def insight_card(
    title: str,
    body: str,
    recommendation: Optional[str] = None,
    tone: str = "information",
    icon: str = "◎"
):

    children = [
        html.Div(
            [
                html.Div(
                    icon,
                    className=(
                        f"insight-icon "
                        f"insight-icon-{tone}"
                    )
                ),
                html.Div(
                    [
                        html.H3(
                            title,
                            className="insight-title"
                        ),
                        html.P(
                            body,
                            className="insight-body"
                        )
                    ]
                )
            ],
            className="insight-main"
        )
    ]

    if recommendation:

        children.append(
            html.Div(
                [
                    html.Span(
                        "Stakeholder interpretation",
                        className="insight-recommendation-label"
                    ),
                    html.P(
                        recommendation,
                        className="insight-recommendation-text"
                    )
                ],
                className="insight-recommendation"
            )
        )

    return html.Div(
        children,
        className=(
            f"insight-card "
            f"insight-card-{tone}"
        )
    )


def methodology_notice(
    title: str,
    message: str,
    tone: str = "information"
):

    return html.Div(
        [
            html.Div(
                "i",
                className=(
                    f"notice-icon "
                    f"notice-icon-{tone}"
                )
            ),
            html.Div(
                [
                    html.Div(
                        title,
                        className="notice-title"
                    ),
                    html.Div(
                        message,
                        className="notice-message"
                    )
                ]
            )
        ],
        className=(
            f"methodology-notice "
            f"methodology-notice-{tone}"
        )
    )


def explanation_panel(
    what_text: str,
    importance_text: str,
    reading_text: str,
    action_text: str
):

    items = [
        (
            "What is this?",
            what_text
        ),
        (
            "Why does it matter?",
            importance_text
        ),
        (
            "How should it be read?",
            reading_text
        ),
        (
            "What should the stakeholder do?",
            action_text
        )
    ]

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        title,
                        className="explanation-question"
                    ),
                    html.Div(
                        body,
                        className="explanation-answer"
                    )
                ],
                className="explanation-item"
            )
            for title, body in items
        ],
        className="explanation-panel"
    )


def filter_group(
    label: str,
    control,
    helper_text: Optional[str] = None
):

    children = [
        html.Label(
            label,
            className="filter-label"
        ),
        control
    ]

    if helper_text:

        children.append(
            html.Div(
                helper_text,
                className="filter-helper"
            )
        )

    return html.Div(
        children,
        className="filter-group"
    )


def hero_header(
    title: str,
    subtitle: str,
    pipeline_text: str,
    platform_text: str,
    latest_date_text: Optional[str] = None
):

    metadata_items = [
        status_pill(
            pipeline_text,
            "success"
        ),
        status_pill(
            platform_text,
            "information"
        )
    ]

    if latest_date_text:

        metadata_items.append(
            status_pill(
                latest_date_text,
                "neutral"
            )
        )

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        "GB POWER SYSTEM INTELLIGENCE",
                        className="hero-eyebrow"
                    ),
                    html.H1(
                        title,
                        className="hero-title"
                    ),
                    html.P(
                        subtitle,
                        className="hero-subtitle"
                    ),
                    html.Div(
                        metadata_items,
                        className="hero-metadata"
                    )
                ],
                className="hero-copy"
            ),
            html.Div(
                [
                    html.Div(
                        "CLOUD ANALYTICS PLATFORM",
                        className="hero-platform-label"
                    ),
                    html.Div(
                        "Azure SQL",
                        className="hero-platform-value"
                    ),
                    html.Div(
                        "Plotly Dash • Flask • Azure App Service",
                        className="hero-platform-detail"
                    )
                ],
                className="hero-platform-card"
            )
        ],
        className="hero-header"
    )


def page_navigation(
    active_page: str
):

    navigation_items = [
        (
            "executive_overview",
            "Executive Overview"
        ),
        (
            "congestion_cost_trends",
            "Congestion and Cost"
        ),
        (
            "stress_cost_relationship",
            "Stress and Cost"
        ),
        (
            "historical_ml_evidence",
            "Historical ML"
        ),
        (
            "etys_planning_context",
            "ETYS Context"
        ),
        (
            "quality_governance",
            "Quality and Governance"
        )
    ]

    return html.Div(
        [
            html.Button(
                label,
                id={
                    "type": "page-navigation-button",
                    "page": page_id
                },
                n_clicks=0,
                className=(
                    "navigation-button active"
                    if page_id == active_page
                    else
                    "navigation-button"
                )
            )
            for page_id, label
            in navigation_items
        ],
        className="page-navigation"
    )


def page_container(
    children: Iterable[Any],
    page_id: str
):

    return html.Main(
        list(children),
        id=f"page-{page_id}",
        className="dashboard-page"
    )


def empty_state(
    title: str,
    message: str
):

    return html.Div(
        [
            html.Div(
                "◇",
                className="empty-state-icon"
            ),
            html.H3(
                title,
                className="empty-state-title"
            ),
            html.P(
                message,
                className="empty-state-message"
            )
        ],
        className="empty-state"
    )
