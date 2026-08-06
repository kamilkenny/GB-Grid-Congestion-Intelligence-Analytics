# GB Grid Congestion and Constraint Cost Intelligence Platform

A machine-learning-enabled cloud intelligence platform for monitoring
transmission-boundary utilisation, available headroom and thermal
constraint costs across Great Britain.

## Project objectives

The platform will:

1. collect and validate NESO open data;
2. store structured records in Azure SQL Database;
3. monitor day-ahead transmission-boundary flows and limits;
4. calculate utilisation and available headroom;
5. analyse thermal constraint costs;
6. display results through an interactive dashboard;
7. evaluate machine-learning models for high-cost event risk;
8. automate ingestion and prediction through GitHub Actions;
9. deploy the completed application on Microsoft Azure.

## Initial NESO datasets

- Day-Ahead Constraint Flows and Limits
- Thermal Constraint Costs
- Electricity Ten Year Statement GB Transmission System Boundaries

## Technology stack

- Python
- Azure SQL Database
- GitHub Actions
- Microsoft Azure
- Streamlit
- Scikit-learn
- Plotly

## Project status

Stage 1 completed:

- repository and project structure created;
- Python environment validated;
- package versions frozen;
- project synchronised with GitHub.

Project status: production dashboard deployed to Azure App Service with GitHub Actions continuous deployment.

## Production cloud application

The completed application is a six page interactive Great Britain grid congestion and thermal constraint cost intelligence dashboard.

It connects directly to eleven approved analytical views in Azure SQL Database and combines forecast congestion exposure, realised thermal constraint costs, historical machine learning evidence and Electricity Ten Year Statement planning projections.

### Application capabilities

* Executive congestion and cost overview
* Historical thermal constraint cost analysis
* Forecast stress and realised cost relationship analysis
* Historical high cost risk score evidence
* Electricity Ten Year Statement planning context and scenario comparison
* Data quality, pipeline and model governance reporting

### Cloud architecture

NESO open data and project source files are processed through the Python data engineering workflow.

The resulting production tables and analytical views are stored in Azure SQL Database.

The Plotly Dash and Flask application reads the approved views and is prepared for deployment to Azure App Service.

### Application location

The production deployment source is stored in:

    app_service/

### Data freshness

The dashboard is live and connected to Azure SQL Database. The current source ingestion process is batch based rather than continuously streaming.

The platform is designed for research, planning and decision support. It is not an official live operational warning system.

### Model governance

The historical high thermal constraint cost risk score is an uncalibrated empirical ranking and is not a literal event probability.

The classifier remains a research dashboard candidate and is not approved for production operational alerting.

### Project author

Model development and dashboard created by Kamil Ridwan Kehinde.

<!-- LIVE_AZURE_DEPLOYMENT_START -->

## Live Azure deployment

The completed Great Britain Grid Congestion and Constraint Cost Intelligence Dashboard is publicly deployed on Microsoft Azure App Service.

Live application:

    https://gb-grid-congestion-kamil-898341.azurewebsites.net

Health endpoint:

    https://gb-grid-congestion-kamil-898341.azurewebsites.net/health

### Production architecture

* Plotly Dash and Flask application
* Azure SQL Database data platform
* Eleven approved analytical SQL views
* Azure App Service Linux deployment
* Gunicorn production server
* GitHub Actions continuous deployment
* OpenID Connect authentication
* Restricted Azure SQL firewall access

### Deployment behaviour

Commits affecting the app_service directory or the deployment workflow automatically trigger validation and deployment from the main branch.

The dashboard is live and database connected. The underlying source ingestion process remains batch based rather than continuously streaming.

The application is a research and decision support platform and is not an official live operational warning system.

<!-- LIVE_AZURE_DEPLOYMENT_END -->


# Great Britain Grid Congestion and Constraint Cost Intelligence Platform

An Azure-based power-system analytics platform integrating NESO
day-ahead congestion indicators, realised thermal constraint costs,
machine-learning evaluation and Electricity Ten Year Statement
planning evidence.

## Live application

**Azure dashboard:**  
https://gb-grid-congestion-kamil-898341.azurewebsites.net

## Project overview

This project examines how forecast congestion pressure across Great
Britain's electricity transmission network relates to realised thermal
constraint costs.

It combines short-term operational evidence, historical cost analysis,
machine-learning performance evaluation and longer-term transmission
planning information within one interactive analytical platform.

The project demonstrates an end-to-end workflow covering:

- NESO open-data discovery and ingestion;
- Python data cleaning and validation;
- feature and indicator engineering;
- Azure SQL Database design;
- approved analytical SQL views;
- chronological machine-learning evaluation;
- Plotly Dash and Flask development;
- GitHub version control;
- secure GitHub Actions authentication through OpenID Connect;
- Azure App Service deployment;
- and post-deployment health validation.

## Core technologies

- Python
- Pandas
- NumPy
- Scikit-learn
- SQLAlchemy
- PyODBC
- Azure SQL Database
- Plotly
- Dash
- Flask
- GitHub Actions
- Microsoft Azure App Service


# Great Britain Grid Congestion and Constraint Cost Intelligence Platform

An Azure-based power-system analytics platform integrating NESO
day-ahead congestion indicators, realised thermal constraint costs,
machine-learning evaluation and Electricity Ten Year Statement
planning evidence.

## Live application

**Azure dashboard:**  
https://gb-grid-congestion-kamil-898341.azurewebsites.net

## Project overview

This project examines how forecast congestion pressure across Great
Britain's electricity transmission network relates to realised thermal
constraint costs.

It combines short-term operational evidence, historical cost analysis,
machine-learning performance evaluation and longer-term transmission
planning information within one interactive analytical platform.

The project demonstrates an end-to-end workflow covering:

- NESO open-data discovery and ingestion;
- Python data cleaning and validation;
- feature and indicator engineering;
- Azure SQL Database design;
- approved analytical SQL views;
- chronological machine-learning evaluation;
- Plotly Dash and Flask development;
- GitHub version control;
- secure GitHub Actions authentication through OpenID Connect;
- Azure App Service deployment;
- and post-deployment health validation.

## Core technologies

- Python
- Pandas
- NumPy
- Scikit-learn
- SQLAlchemy
- PyODBC
- Azure SQL Database
- Plotly
- Dash
- Flask
- GitHub Actions
- Microsoft Azure App Service


## Solution architecture

```mermaid
flowchart LR
    A[NESO Open Data] --> B[Python Ingestion]
    B --> C[Validation and Cleaning]
    C --> D[Feature Engineering]
    D --> E[Azure SQL Database]

    E --> F[Approved Analytical Views]
    F --> G[Plotly Dash and Flask]
    G --> H[Azure App Service]

    D --> I[Machine Learning Evaluation]
    I --> E

    J[GitHub Repository] --> K[GitHub Actions]
    K -->|OIDC Authentication| H
    K --> L[Public Health Validation]



---

## Add a dashboard section to the README

```markdown
## Dashboard pages

### Executive Overview

Provides a stakeholder-focused summary of forecast congestion
exposure, realised thermal constraint cost, high-cost events,
historical risk scores and data availability.

### Congestion and Cost

Examines daily, monthly, seasonal and financial-year patterns using
trend charts, rankings, calendar heatmaps and an exportable evidence
table.

### Stress and Cost

Explores historical relationships between forecast exposure
indicators and realised thermal constraint costs.

### Machine Learning Performance Analysis

Displays the historical risk-score timeline, confusion matrix,
score-band event rates, classification metrics and formal
model-governance outcome.

### Electricity Ten Year Statement Context

Examines boundary capability, future transfer requirements, planning
scenarios and projected capability gaps.

### Quality and Governance

Documents data-quality issues, pipeline status, analytical
definitions, model restrictions and interpretation boundaries.

## Microsoft Azure implementation

Azure is a core part of the platform architecture.

### Azure SQL Database

Azure SQL Database stores the structured analytical data and exposes
approved views to the dashboard. The application does not query raw
source tables directly.

### Azure App Service

The Dash and Flask application is hosted on Azure App Service using a
Linux Python environment.

### Secure configuration

Database credentials and deployment configuration are supplied through
environment variables and Azure App Settings rather than being stored
in the repository.

### GitHub Actions and OpenID Connect

GitHub Actions authenticates with Azure through OpenID Connect and a
federated identity. This avoids storing a permanent Azure deployment
password in GitHub.

The workflow:

1. checks out the repository;
2. validates the Python application files;
3. creates an Azure deployment package;
4. authenticates with Azure;
5. deploys to Azure App Service;
6. and validates the public health endpoint.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Azure SQL](https://img.shields.io/badge/Azure-SQL%20Database-0078D4)
![Azure App Service](https://img.shields.io/badge/Azure-App%20Service-0078D4)
![Dash](https://img.shields.io/badge/Plotly-Dash-3F4F75)
![Machine Learning](https://img.shields.io/badge/Machine%20Learning-Scikit--learn-orange)
![Deployment](https://img.shields.io/badge/Deployment-Live-success)


[![Deploy to Azure](https://github.com/kamilkenny/GB-Grid-Congestion-Intelligence-Analytics/actions/workflows/deploy-azure-app-service.yml/badge.svg)](https://github.com/kamilkenny/GB-Grid-Congestion-Intelligence-Analytics/actions/workflows/deploy-azure-app-service.yml)







    
