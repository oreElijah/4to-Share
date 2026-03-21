from app.main import create_app

app = create_app()

__all__ = [
    "app"
            ]

@app.get("/")
async def root():
    return {"message": "Welcome to the 4to Share API!"}