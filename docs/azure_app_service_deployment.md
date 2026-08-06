# Azure deployment source

The production Azure App Service application is located inside the app_service directory.

Application entry point:

    app_service/app.py

Flask server object:

    app:server

Recommended Azure startup command:

    gunicorn --chdir app_service --bind=0.0.0.0:$PORT --workers=2 --threads=4 --timeout=180 app:server

Required Azure App Service environment variables:

    AZURE_SQL_SERVER
    AZURE_SQL_DATABASE
    AZURE_SQL_USERNAME
    AZURE_SQL_PASSWORD

Health check path:

    /health
