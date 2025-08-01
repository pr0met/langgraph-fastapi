# FastAPI LangGraph Agent Prototype

This project is a prototype implementation of a LangGraph agent within a FastAPI server, complete with a minimalist conversational web UI.

## Installation

To install the required dependencies, use `uv`:

```bash
uv pip sync requirements.txt
```

## Configuration

1.  **Google API Key**: Add your Gemini API key to your environment variables.

    ```bash
    export GOOGLE_API_KEY="..."
    ```

2.  **LumApps Bearer Token**: Add your LumApps bearer token to your environment variables.

    ```bash
    export LUMAPPS_TOKEN="..."
    ```

## Running the Application

To start the FastAPI server, run the following command:

```bash
uvicorn server:app --reload
```

## Accessing the Web UI

The conversational web UI is available at:

[http://localhost:8000/](http://localhost:8000/)