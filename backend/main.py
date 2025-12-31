from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}


    response = requests.post(url, json=payload, headers=headers)
    return response.json()
