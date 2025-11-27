# UDO API

FastAPI backend for Unternehmensdaten SaaS service.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the API

Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Available Endpoints

- `GET /` - Root endpoint with API info
- `GET /health` - Health check endpoint
- `GET /api/dummy` - Dummy endpoint with sample data

## Repository

Git repository: git@github.com:CarstenVogelsang/udo__api.git
