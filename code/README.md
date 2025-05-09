# code

This is the folder that contains all the source code for the API, the LLM inference and the platform logic.

# Getting started

This folder contains the backend code for the Hack2m platform. Follow these instructions to get the project running locally.

## Prerequisites

- **Python 3.11**
  You can use `uv` to install the correct version. The project uses `.python-version` to specify the version.
- **Docker**
  Required to run the database, a code runner for 1 of the challenges, and Nginx services. [Install Docker](https://docs.docker.com/get-docker/).

  Tip: the service is coded to run on Windows. So, install Docker Desktop on Windows preferably.
- **Docker Compose**
  Usually included with Docker Desktop, or install separately if needed.
- **uv**
  This project uses [astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) as the Python dependency manager. Follow their instructions to install `uv`.
- **CUDA**
  This projects is built relying on GPU-acceleration to run the LLM model, and there are libraries compiled with GPU. So installing the CUDA software for your GPU is needed. You can download at the [NVIDIA](https://developer.nvidia.com/cuda-downloads) official page.
- **.env file**
  You may need a `.env` file at the project root for environment variables (e.g., database credentials). There's a `.env.example` that should work out-of-the-box.

  Tip: should be renamed `.env.example` --> `.env`

## Build and start Docker services

From the `docker` directory, build and start the required services (Postgres and Nginx):

```bash
cd docker
# Build the image for the Python runner (needed for 1 challenge)
docker build -t python-runner .
# Build the Nginx image (if not already built)
cd local
docker build -t nginx-hack2m:v0.1.0 .
```

Start all services (db, nginx) from `docker` folder:
```bash
cd docker
docker-compose up -d
```

This will start the database and Nginx containers in the background.

## Install Python dependencies

Using `uv`, we can create a virtual environment (venv) with all the required dependencies isolated from your environment.

From the `code` directory, install all dependencies using `uv`:

```bash
cd code
uv sync
```

## Run the FastAPI server

From the `code` directory, start the FastAPI server with:

```bash
cd code
uv run uvicorn main:app --reload
```

The API will be available at [http://localhost:8000/api](http://localhost:8000/api).

---

If you encounter issues, check that all prerequisites are installed and that Docker services are running. For more details, see the main project README.
