from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from llama.model import ModelFactory
from logging import Logger, basicConfig, INFO


basicConfig(level=INFO, format="%(asctime)s %(levelname)s - %(message)s")
logger = Logger("fastapi")

FLAG = "f{ab2e902eacbed29bb29043aba324ad32}"
model = ModelFactory()

@asynccontextmanager
async def lifespan(app: FastAPI):
    model.load()
    yield

    model.clear()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root() -> dict:
    return {"message": "Hello World"}

@app.get("/question")
async def question(question: str, version: str) -> dict:
    try:
        response = model.ask(question)
        return {"response": response}
    except Exception as e:
        logger.error("Unexpected error", e)
        raise HTTPException(500, "Unexpected error")

@app.get("/check")
async def check_flag(flag: str) -> dict:
    if flag == FLAG:
        return {"result": "Enhorabuena! Has superado el reto"}
    else:
        return {"result": "Vaya, no es correcto :( Vuelve a intentarlo!"}
