from app.core.api import MiroAPI
from app.db.session import db
from app.core.logger import logger

# Create an instance of the MiroAPI application
app = MiroAPI()
app.configure()

if __name__ == "__main__":
    try:
        # Create the database tables before starting the FastAPI application
        db.create_database()

        # Start the FastAPI application using uvicorn
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    except Exception as e:
        logger.error(f'Error during application startup: {str(e)}')
