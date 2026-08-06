# Azure App Service Deployment Guide

## Required application settings

Configure these values in Azure App Service under Environment variables:

    AZURE_SQL_SERVER
    AZURE_SQL_DATABASE
    AZURE_SQL_USERNAME
    AZURE_SQL_PASSWORD
    SCM_DO_BUILD_DURING_DEPLOYMENT=true

## Startup command

    gunicorn --bind=0.0.0.0:$PORT --workers=2 --threads=4 --timeout=180 app:server

## Health check

Set the App Service health check path to:

    /health

## Deployment source

Connect the GitHub repository through Azure App Service Deployment Center and select the main branch.

## Security

Do not place database credentials inside app.py, database.py, README.md, workflow files or committed environment files.
