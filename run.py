"""Entry point for running the application with uvicorn."""
from app import server

# The ASGI application for uvicorn
application = server

if __name__ == "__main__":
    import uvicorn
    from config import Config
    
    uvicorn.run(
        "run:application",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG
    )
