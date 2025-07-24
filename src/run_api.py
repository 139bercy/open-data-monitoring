"""
Script de lancement de l'API Open Data Monitoring
"""

import uvicorn
from interfaces.api.main import api_app
from settings import ENV
import os

if __name__ == "__main__":
    # Configuration adaptée à l'environnement
    config = {
        "app": "interfaces.api.main:api_app",
        "host": "0.0.0.0",
        "port": os.environ["API_PORT"],
    }
    
    if ENV == "DEV":
        config.update({
            "reload": True,
            "log_level": "debug"
        })
    
    print(f"🚀 Lancement de l'API Open Data Monitoring ({ENV})")
    print(f"📍 URL: http://localhost:{os.environ['API_PORT']}")
    print(f"📚 Documentation: http://localhost:{os.environ['API_PORT']}/docs")
    
    uvicorn.run(**config) 