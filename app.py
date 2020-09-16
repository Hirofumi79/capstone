from fastapi import FastAPI, Path
from starlette.responses import RedirectResponse
from pydantic import BaseModel

from src.model import train_model, predict_model, fetch_data

app = FastAPI(
        title="capstone",
        description="Model API for Capstone Project",
        version="0.0.1",
        docs_url="/swagger",
        redoc_url=None
)

@app.get("/", include_in_schema=False)
def read_root():
    response = RedirectResponse(url='/swagger')
    return response

@app.get("/status")
async def status():
    return {"status": "ok"}

class PredictInput(BaseModel):
    country: str
    horizon: int

@app.post('/predict')
def predict(args: PredictInput):
    args = args.dict()
    country = args['country']
    result = predict_model(args['horizon'], 'model_'+country)
    return list(result)

class TrainInput(BaseModel):
    country: str

@app.post('/train')
def train(args: TrainInput):
    args = args.dict()
    country = args['country']
    data_path = 'data/intermediate/clean_train_data_' + country + '.csv'
    model_name = 'model_' + country
    X = fetch_data(data_path)
    mse = train_model(X, model_name)
    return {'MSE': mse}
