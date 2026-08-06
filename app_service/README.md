# Great Britain Grid Congestion and Constraint Cost Intelligence Dashboard

## Overview

This cloud connected dashboard helps stakeholders understand how forecast congestion across Great Britain's electricity network relates to realised thermal constraint costs.

It combines historical congestion and cost trends, machine learning evaluation evidence, and Electricity Ten Year Statement planning projections in one interactive decision support platform.

The application is connected directly to Azure SQL Database. Its current source ingestion process is batch based, so it is not a continuously streaming or official live operational warning system.

## Dashboard pages

1. Executive Overview
2. Congestion and Cost Trends
3. Stress and Cost Relationship
4. Historical Machine Learning Evidence
5. Electricity Ten Year Statement Planning Context
6. Data Quality and Governance

## Technology

Python, pandas, Plotly, Dash, Flask, SQLAlchemy, pyodbc, Azure SQL Database, Azure App Service, Gunicorn and GitHub.

## Local setup

Install the dependencies:

    pip install -r requirements.txt

Configure these environment variables:

    AZURE_SQL_SERVER
    AZURE_SQL_DATABASE
    AZURE_SQL_USERNAME
    AZURE_SQL_PASSWORD

Run the application:

    python app.py

Open:

    http://127.0.0.1:8050

## Health endpoint

The application health endpoint is:

    /health

## Model governance

The historical high thermal constraint cost risk score is an uncalibrated empirical ranking, not a literal probability.

The classifier is retained as a research dashboard candidate and is not approved for production operational alerting.

## Electricity Ten Year Statement context

Electricity Ten Year Statement projections are presented as long term planning context. No approved mapping exists between the daily operational constraint groups and Electricity Ten Year Statement boundaries.

## Security

Azure SQL credentials must be stored in Azure App Service environment settings and must never be committed to GitHub.

## Author

Model development and dashboard created by Kamil Ridwan Kehinde.
