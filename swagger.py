from flask import Flask
from flask_apispec import APISpec, MarshmallowPlugin
from flask_apispec.extension import FlaskApiSpec
from models import User, Portfolio, Transaction, MarketData, Recommendation, RiskAnalysis
from app import app, ma

# Initialize APISpec
spec = APISpec(
    title='Financial AI Dashboard API',
    version='1.0',
    plugins=[MarshmallowPlugin()],
    openapi_version='2.0.0'
)

# Register models with APISpec
with app.app_context():
    for model in [User, Portfolio, Transaction, MarketData, Recommendation, RiskAnalysis]:
        ma.SQLAlchemyAutoSchema(model)
    
    # Add routes to spec
    from app import register, login, portfolios, portfolio, transactions, market_data, \
         recommendations, risk_analyses, vector_news, vector_conversations, vector_recommendations
    
    for route in [register, login, portfolios, portfolio, transactions, market_data, 
                recommendations, risk_analyses, vector_news, vector_conversations, vector_recommendations]:
        spec.path(view=route)

    # Save OpenAPI spec
    with open('openapi.yaml', 'w') as f:
        f.write(spec.to_yaml())

    # Register Swagger UI route
    @app.route('/docs')
    def swagger():
        return app.send_static_file('swagger-ui.html')
