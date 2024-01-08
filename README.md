DAVID

# Service
Backend service for the DAVID project, writting in Python >= 3.10, using FastAPI as WSGI Framework.

## Get Started
Make sure you have Conda installed, I recommand using Mamba as a replacement for Conda. Follow this (link)[https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html]
1. Once you have Mamba installed. Navigate to `service` folder and run `mamba env create -f environment.yml`
2. Then run `poetry install` to install the dependencies.
3. Alternatively, use (`ruff`)[https://github.com/astral-sh/ruff] as linter and formatter for Python. Run `ruff .` to lint and format the code in `serivce`.


# Web
Frontend web application for the DAVID project, writting in TypeScript, using NextJS as React Framework and Flowbies as UI Framework.


# API Design
1. `GET /api/v1/health` - Health check endpoint
2. `GET /api/v1/` - Get all the available endpoints 
3. `POST /api/v1/topic` - Create a topic
4. `POST /api/v1/document` - Upload a document, tied to a certain topic
5. `POST /api/v1/media` - Upload a document, tied to a certain topic
