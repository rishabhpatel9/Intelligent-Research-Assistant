# Intelligent Research Assistant

A GenAI powered intelligent agent that dynamically automates complex research workflows by intelligently searching, summarizing, fact checking, and synthesizing information.

## Overview

I built this platform to automate complex research workflows and make deep analysis accessible. Instead of just answering basic questions, it acts as a local first intelligent agent that dynamically figures out how to solve a problem. When given a request, the system analyzes the input at runtime to choose the best strategy: searching the web for live data, compressing dense documents into summaries, rigorously fact checking claims, or combining multiple approaches for a deep synthesis.

## Core Features & Capabilities

* **Dynamic Query Routing:** The core interaction loop is governed by an intelligent classifier that accurately routes requests to specialized modules based on user intent.
  * **Search Module:** Specialized for retrieving current, latest, or recent information directly from web sources.
  * **Summarize Module:** Built for condensing long texts, documents, or PDFs. If you don't have enough data on the topic, the system will look up relevant information online and then summarize it for you.
  * **Fact Check Module:** Dedicated to rigorous verification of claims using trusted references.
  * **Hybrid Workflow:** Combines search, summary, and fact-checking to tackle complicated, multi-part questions.
* **Structured, Publication-Ready Output:** The assistant automatically formats its intelligence into polished reports incorporating executive summaries, bulleted insights, tables for data-heavy concepts, and strict citations to ensure credibility.
* **Progressive Web App (PWA) Frontend:** Our refined Gradio interface provides a modern, responsive, and application-like experience. The UI features a carefully crafted "Soft" theme with slate and gray aesthetics, an optimized reading layout, and Markdown-rendered outputs.

## Technology Stack

This project leverages a modern, highly optimized technology stack:

* **LangGraph:** Orchestrates our multi-step agentic workflows, branching logic, and runtime state management.
* **LangSmith:** Provides deep transparency, debugging, and evaluation metrics into the agent's internal reasoning traces.
* **FastAPI & Pydantic:** Powers the robust, type-checked backend REST API for processing query requests.
* **Gradio:** Drives the user-facing web interface and seamless Progressive Web App (PWA) functionality.
* **LM Studio:** Powers local LLM integration for privacy first natural language understanding and generation, bypassing the need for external APIs. Smart resource usage with 'Just in time' model loading.
* **BeautifulSoup4 & Requests:** Drives external web-scraping and internal HTTP communication.
* **Python & UV:** The foundation of the system, utilizing standard Python built securely and quickly with the UV package manager.
* **Docker:** Facilitates system-agnostic reproducibility and streamlined deployment.

## System Architecture

```text
                       ┌───────────────────────────┐
                       │   User Query (Gradio UI)  │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │   Query Classifier        │
                       │   (fact-check, search,    │
                       │   summarize, hybrid)      │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │   LangGraph Orchestration │
                       │   (runtime branching,     │
                       │   multi-step workflows)   │
                       └─────────────┬─────────────┘
                                     │
        ┌──────────────────┬─────────┴────────┬──────────────────┐
        ▼                  ▼                  ▼                  ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ Search Module  │ │ Summarization  │ │ Fact-Check     │ │ Hybrid Workflow│
│ (web sources)  │ │ (docs, PDFs)   │ │ (trusted refs) │ │ (combine paths)│
└───────┬────────┘ └───────┬────────┘ └───────┬────────┘ └───────┬────────┘
        │                  │                  │                  │
        └────────────────┬─┴─────────┬────────┴─┬────────────────┘
                         ▼           ▼          ▼
                       ┌───────────────────────────┐
                       │   LangSmith Evaluation    │
                       │   (trace reasoning,       │
                       │   debug, metrics)         │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │   Structured Output Gen   │
                       │   (summary, bullets,      │
                       │   tables, citations)      │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │   Gradio Frontend Report  │
                       │   (executive summary,     │
                       │   recruiter-facing polish)│
                       └───────────────────────────┘
```

### Workflow Graph (LangGraph)

![Workflow Graph](./assets/workflow_graph.png)

## Getting Started

### Prerequisites

* Python 3.13+ installed
* [uv](https://github.com/astral-sh/uv) package manager installed
* Docker & Docker Compose (if using containerized deployment)
* Tavily API Key
* Local LM Studio instance running

### 1. How to run locally

First, clone the repository and navigate into the directory:

```bash
git clone <repository-url>
cd Intelligent-Research-Assistant
```

Setup your environment variables by copying `example.env` to `.env`:

```bash
cp example.env .env
```
Ensure you add your `TAVILY_API_KEY` inside `.env`. Provide your Langsmith flags if you are leveraging them as well.

Next, install the required dependencies using the `uv` package manager:

```bash
uv sync
```

**Run the Backend:**
Start the backend server. It will listen on port `8000`.

```bash
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Run the Frontend:**
In a separate terminal window, start the Gradio frontend application. It will run on port `7860`.

```bash
uv run python frontend/app.py
```

Access the frontend via your browser at `http://127.0.0.1:7860`.

### 2a. How to deploy on Docker

If you prefer to deploy the services individually using Docker, you can build and run them utilizing their respective `Dockerfile`s.

**Backend Build & Run:**
Ensure you are in the project's root directory so that docker context is correct.

```bash
docker build -t intelligent-research-backend -f backend/Dockerfile .

# Run the container locally, exposing it on 8000 and passing in your .env variables
docker run -d -p 8000:8000 --name backend-service --env-file .env intelligent-research-backend
```

**Frontend Build & Run:**
Navigate into the frontend directory to build the frontend.

```bash
cd frontend
docker build -t intelligent-research-frontend .
cd ..

# Run the frontend container
# Pass the correct API_URL if backend address is different
docker run -d -p 7860:7860 --name frontend-service -e API_URL=http://<host.docker.internal_or_backend_ip>:8000/query intelligent-research-frontend
```

### 2b. How to deploy using Docker Compose

Docker Compose is the most straightforward mechanism to spin up the entire environment together.

Inside the root directory, simply run:

```bash
docker-compose up --build -d
```

Running this command will automatically:
1. Build both the `frontend` and `backend` images.
2. Link them together seamlessly within a local docker network.
3. Handle environment variable exposure using `.env`.
4. Deploy the Application UI at `http://localhost:7860`.

To safely stop and remove the containers once you're done, run:

```bash
docker-compose down
```
