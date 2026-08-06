# Azure App Service deployment

## Production application

The Great Britain Grid Congestion and Constraint Cost Intelligence Dashboard is deployed to:

    https://gb-grid-congestion-kamil-898341.azurewebsites.net

## Deployment source

The production application source is located in:

    app_service/

## Runtime

    Python 3.12

## Startup command

    gunicorn --bind=0.0.0.0:$PORT --workers=2 --threads=4 --timeout=180 --access-logfile - --error-logfile - app:server

## Health monitoring

    /health

The health endpoint validates the application, the Azure SQL connection and access to the eleven approved analytical views.

## Continuous deployment

GitHub Actions deploys changes from the main branch using OpenID Connect authentication.

Workflow:

    .github/workflows/deploy-azure-app-service.yml

## Security

No Azure password or Azure SQL password is stored in the GitHub workflow.

The GitHub deployment identity has Website Contributor access scoped to the dedicated Azure Web App.

Azure SQL access is restricted to the App Service outbound IP addresses.
