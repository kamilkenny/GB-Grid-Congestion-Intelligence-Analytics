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
- ETYS GB Transmission System Boundaries

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

Current stage: Stage 6C, cloud application integration and Azure App Service deployment.

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
