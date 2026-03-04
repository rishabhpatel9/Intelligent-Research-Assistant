# Project Overview

The Intelligent Research Assistant is a GenAI powered agent designed to automate research workflows.  
Instead of simply answering questions, the system dynamically decides at runtime how to approach a problem - whether to search the web, summarize documents, fact-check claims, or combine multiple strategies.  

Key technologies:
- **LangGraph** → Orchestrates multi-step workflows with branching logic.
- **LangSmith** → Provides evaluation, debugging, and transparency into agent reasoning.
- **LM Studio (local LLM)** → Powers natural language understanding and generation without relying on external APIs.
- **Gradio** → Frontend interface for user queries and polished report outputs.
- **Docker** → Ensures reproducibility and easy deployment.

The assistant produces structured reports with:
- Executive summaries
- Bullet point insights
- Tables for data heavy queries
- Citations for credibility

# Planned System Architecture

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
