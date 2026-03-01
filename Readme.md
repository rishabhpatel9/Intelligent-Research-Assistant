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
          ┌────────────────┬─────────┴─────────┬──────────────────┐
          ▼                ▼                   ▼                  ▼
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
