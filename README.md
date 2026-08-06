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
