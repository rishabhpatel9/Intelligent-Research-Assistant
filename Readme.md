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
