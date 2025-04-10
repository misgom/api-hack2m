# api-hack2m

Hack2m (HackLLM using LL as roman number II) is a CTF platform for LLM Hacking to learn about LLM vulnerabilities and complete hacking challenges.

## Description

This repository contains the backend for the platform and is built with FastAPI and served using Uvicorn, the platform is designed to be lightweight, fast, and highly scalable to support dynamic hacking scenarios.

The backend provides essential functionalities to host, manage, and evaluate challenges, as well as handle user interactions in real-time.

## Installation

To install the project with the dependencies this project uses `uv` as dependecy manager. So run:

```bash
uv install
```

## Run

To run the API just run:

```bash
uv run uvicorn main:app --reload
```
