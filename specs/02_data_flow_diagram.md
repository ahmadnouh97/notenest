## 📊 Data Flow Diagram – NoteNest

[User Shares Link]  
       │  
       ▼  
[Share Intent Handler in App]  
       │  URL + Title
       ▼  
[LLM API Call: Summarize Link]  
       │  Summary (optional tags)
       ▼  
[Editable Summary Screen]  
       │  (User edits / rephrases)
       ▼  
[Save Button Pressed]  
       │  
       ▼  
 ┌──────────────────────────────────────────┐
 │      Local SQLite Database (Notes)       │
 │------------------------------------------│
 │ id | url | title | summary | tags | date │
 └──────────────────────────────────────────┘  
       │  
       ├──► [Embedding Generation (LLM or local model)]  
       │         │  
       │         ▼  
       │   ┌─────────────────────┐  
       │   │ Embeddings Table    │  
       │   │ note_id | vector[]  │  
       │   └─────────────────────┘  
       │  
       ▼  
[Main Screen: View & Search Notes]  
       │  
       ├── Keyword search → DB query  
       └── Semantic search → Embedding similarity match  
              ▼  
        Filtered Note List  

## Chat Tab Data Flow

[User enters query in Chat Tab]  
       │  
       ├──► Generate embedding for query  
       │  
       ├──► Semantic match in Embeddings Table → Retrieve top N notes  
       │  
       └──► Send (Query + Relevant Notes) → LLM API  
                  │  
                  ▼  
          AI-generated answer in chat  
