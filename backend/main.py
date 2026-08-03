from fastapi import FastAPI

app = FastAPI(title="Lyrics Music Exploration API")

@app.get("/health")
def health():
    return {"status": "ok"}