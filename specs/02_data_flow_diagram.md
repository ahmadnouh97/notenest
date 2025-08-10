## 📊 Data Flow Diagram – NoteNest

[User Shares Link]  
       │  
       ▼  
[Web Form Submission]  
       │  URL + Title
       ▼  
[FastAPI `/summarize`: Summarize Link]  
       │  Summary (optional tags)
       ▼  
[Editable Summary Screen]  
       │  (User edits / rephrases)
       ▼  
[Save Button Pressed]  
       │  
       ▼  
 ┌──────────────────────────────────────────┐
  │      Supabase Postgres (Notes)           │
  │------------------------------------------│
  │ id | user_id | url | title | summary | tags | created_at |
 └──────────────────────────────────────────┘  
       │  
        ├──► [Embedding Generation via FastAPI `/embed` (OpenAI) or local fallback]  
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
        ├── Keyword search → Postgres full-text / ILIKE  
        └── Semantic search → pgvector cosine similarity  
              ▼  
        Filtered Note List  

## Chat Tab Data Flow

[User enters query in Chat Tab]  
       │  
       ├──► Generate embedding for query  
       │  
       ├──► Semantic match in Embeddings Table → Retrieve top N notes  
       │  
        └──► Send (Query + Relevant Notes) → FastAPI `/chat` (OpenAI)  
                  │  
                  ▼  
          AI-generated answer in chat  
