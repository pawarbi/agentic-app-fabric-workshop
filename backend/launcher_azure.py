from werkzeug.serving import run_simple

def create_combined_app():
    """Create combined WSGI application"""
    # Import apps
    import banking_app
    import agent_analytics
    
    # Initialize databases
    with banking_app.app.app_context():
        banking_app.db.create_all()
        print("✅ Banking database tables initialized")
        
        # Run data ingestion
        try:
            from init_data import check_and_ingest_data
            check_and_ingest_data()
            print("✅ Data initialization complete")
        except Exception as e:
            print(f"⚠️ Data initialization warning: {e}")
    
    with agent_analytics.app.app_context():
        agent_analytics.db.create_all()
        agent_analytics.initialize_tool_definitions()
        agent_analytics.initialize_agent_definitions()
        print("✅ Analytics database tables initialized")
    
    # Create combined app with URL prefixes
    application = DispatcherMiddleware(banking_app.app, {
        '/analytics': agent_analytics.app
    })
    
    return application

def run_combined_services():
    """Entry point for Gunicorn"""
    return create_combined_app()

# For local development
if __name__ == '__main__':
    app = create_combined_app()
    port = int(os.environ.get('PORT', 8000))
    run_simple('0.0.0.0', port, app, use_reloader=False, use_debugger=True)