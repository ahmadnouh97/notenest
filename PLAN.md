# 🚀 NoteNest Project Implementation Plan

## 📋 Project Overview

**NoteNest** is a personal link-saving app with a built-in AI assistant that helps users capture links from their phone, summarize or describe them, and find them later using semantic search or by chatting with their notes.

**Target Platforms:** Android (primary) + Web (PWA)
**Architecture:** Single codebase using React Native + React Native Web

## 🎯 Core Features (MVP)

### 1. Link Capture & Processing
- Android share intent integration
- URL and title extraction
- AI-powered link summarization using OpenAI API
- Editable summary with AI rephrasing capability

### 2. Note Management
- **Local storage**: SQLite (Android) / IndexedDB (Web) for offline access
 - **Cloud sync**: Supabase (Free tier) for cross-device synchronization
- Tag-based organization
- Rich note metadata (URL, title, summary, tags, creation date)
- **Real-time sync**: Changes sync automatically across devices

### 3. Intelligent Search
- Keyword-based search
- Semantic search using embeddings
- Real-time filtering and results display

### 4. AI Chat Interface
- Natural language queries about saved notes
- Context-aware responses using retrieved note content
- Continuous knowledge growth

## 🏗️ Technical Architecture

### Frontend Stack
- **React Native** with **React Native Web** for cross-platform compatibility
- **Expo** for development, builds, and deployment
- **TypeScript** for type safety and shared types
- **Tamágui** or **Dripsy** for cross-platform UI components

### Backend & Storage
- **Local Storage**: SQLite (Android) via `expo-sqlite` / IndexedDB (Web) via web shim
 - **Cloud Database**: Supabase (Free tier: Postgres + Auth + Realtime + Edge Functions) for cross-device sync
 - **Storage abstraction layer** for unified API across platforms
 - **Sync Engine**: Real-time synchronization with conflict resolution (Supabase Realtime)
 - **Offline Support**: Local-first architecture with background sync

### AI Integration
- **OpenAI API** integration:
  - `gpt-4o-mini` for summaries and rephrasing
  - `text-embedding-3-small` for vector embeddings
- **Local semantic search** using cosine similarity

### Data Models
```sql
-- Local SQLite/IndexedDB tables
-- Notes table
CREATE TABLE notes (
  id TEXT PRIMARY KEY, -- UUID v7 for cross-device sync
  url TEXT NOT NULL,
  title TEXT,
  summary TEXT,
  tags TEXT, -- JSON array as string
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  sync_status TEXT DEFAULT 'synced', -- 'synced' | 'pending' | 'conflict'
  version INTEGER DEFAULT 1,
  is_deleted INTEGER DEFAULT 0,
  deleted_at TEXT
);

-- Embeddings table (local)
CREATE TABLE embeddings (
  note_id TEXT PRIMARY KEY,
  vector TEXT NOT NULL, -- JSON array as string
  FOREIGN KEY (note_id) REFERENCES notes(id)
);
CREATE INDEX IF NOT EXISTS idx_notes_updated_at ON notes(updated_at);
CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at);

-- Cloud Database Schema (Supabase Postgres)
-- Table: profiles (managed by Supabase Auth)
-- id (uuid, PK)

-- Table: notes
-- id (uuid, PK), user_id (uuid, FK -> auth.users.id), url, title, summary, tags jsonb,
-- created_at timestamptz, updated_at timestamptz, version int, is_deleted boolean, deleted_at timestamptz

-- Table: embeddings
-- note_id (uuid, PK, FK -> notes.id), vector vector(1536) -- using pgvector extension

-- RLS Policies (per-user isolation)
-- enable row level security on notes, embeddings; allow user = auth.uid()
```

## 📱 User Interface Design

### Main Screen
- Search box at the top
- Scrollable list of note cards
- Each card displays: thumbnail, title, summary, tags
- Add note button (floating action button)

### Edit Screen
- Summary input field (pre-filled with AI summary)
- Rephrase button for AI assistance
- Save button
- Tag management

### Chat Tab
- Natural language input field
- Chat history display
- AI-generated responses with note references

## ☁️ Cloud Sync Architecture (Free Tier)

### Sync Strategy
- **Local-First Architecture**: All operations happen locally first, then sync to cloud
- **Real-time Sync**: Changes sync automatically across devices using Supabase Realtime
- **Offline Support**: App works offline, syncs when connection is restored
- **Conflict Resolution**: Handles simultaneous edits from multiple devices

- **User Accounts**: Email/password (Supabase Auth). Social logins optional; free tier supports Google/others with limits.
- **Data Isolation**: Each user's notes are completely private
- **Secure API**: All cloud communication uses HTTPS and authentication tokens
- **Data Encryption**: Sensitive data encrypted in transit and at rest

### Sync Engine Components
- **Sync Queue**: Manages pending sync operations (local queue persisted in SQLite/AsyncStorage)
- **Conflict Resolver**: Handles simultaneous edits (last-write-wins with version checks + user notification)
- **Background Sync**: Automatic sync when app regains focus/connectivity; Android via expo-background-fetch
- **Delta Sync**: Only sync changed data using `updated_at > last_sync_at`

## 🔄 Data Flow Architecture

### Link Capture Flow
1. User shares link → Share intent handler
2. Extract URL + title
3. Call OpenAI API for summarization
4. Present editable summary screen
5. Save to local database
6. Generate and store embeddings
7. **Queue for cloud sync** (background process)
8. **Upload to cloud database** when online

### Search Flow
1. User enters search query
2. Generate query embedding
3. **Search local database first** (fast response)
4. **Sync with cloud** if needed (background)
5. Perform semantic similarity search
   - Offline: client-side cosine similarity against local embeddings
   - Online: optionally query Supabase (pgvector) for server-side similarity
6. Filter and display results

### Chat Flow
1. User enters natural language query
2. Generate query embedding
3. **Search both local and cloud databases**
4. Retrieve relevant notes via semantic search (client-side or via Supabase pgvector)
5. Route OpenAI calls through a Supabase Edge Function (do not expose API key in client)
6. Display AI response

## 📁 Project Structure

```
notenest/
├── src/
│   ├── components/          # Reusable UI components
│   ├── screens/             # Screen components
│   ├── services/            # Business logic and API calls
│   ├── database/            # Storage abstraction layer
│   ├── sync/                # Cloud sync engine
│   ├── auth/                # User authentication
│   ├── ai/                  # AI integration and embeddings
│   ├── types/               # TypeScript type definitions
│   ├── utils/               # Helper functions
│   └── navigation/          # Navigation configuration
├── assets/                  # Images, fonts, etc.
├── docs/                    # Documentation
├── specs/                   # Project specifications
├── app.json                 # Expo configuration
├── package.json             # Dependencies
└── tsconfig.json            # TypeScript configuration
```

## 🚀 Implementation Phases

### Phase 1: Foundation & Setup (Week 1-2)
- [ ] Project initialization with Expo
- [ ] TypeScript configuration
- [ ] Basic project structure setup
- [ ] Dependencies installation
- [ ] Storage abstraction layer implementation
- [ ] Basic database schema setup

### Phase 2: Core Infrastructure (Week 3-4)
- [ ] OpenAI API integration
- [ ] Embedding generation and storage
- [ ] Semantic search implementation
- [ ] Basic note CRUD operations
- [ ] Storage layer testing
 - [ ] **Cloud database setup** (Supabase Free tier)
 - [ ] **User authentication system** (Supabase Auth)

### Phase 3: User Interface (Week 5-6)
- [ ] Main screen implementation
- [ ] Note editing interface
- [ ] Search functionality UI
- [ ] Basic navigation setup
- [ ] Cross-platform UI testing

### Phase 4: AI Features (Week 7-8)
- [ ] Link summarization integration
- [ ] AI rephrasing functionality
- [ ] Chat interface implementation
- [ ] Context-aware AI responses
- [ ] AI feature testing
- [ ] **Cloud sync engine implementation**
- [ ] **Conflict resolution system**

### Phase 5: Android Integration (Week 9-10)
- [ ] Share intent handler implementation
- [ ] Android-specific optimizations
- [ ] SQLite integration testing
- [ ] Android build and testing

### Phase 6: Web PWA (Week 11-12)
- [ ] React Native Web integration
- [ ] IndexedDB implementation
- [ ] PWA configuration
- [ ] Web-specific testing
- [ ] Cross-platform compatibility testing

### Phase 7: Polish & Testing (Week 13-14)
- [ ] UI/UX refinements
- [ ] Performance optimization
- [ ] Error handling improvements
- [ ] Comprehensive testing
- [ ] Bug fixes and refinements

## 🛠️ Development Tools & Dependencies

### Core Dependencies (all free-tier compatible except OpenAI)
```json
{
  "expo": "^50.0.0",
  "react-native": "0.73.0",
  "react-native-web": "^0.19.0",
  "expo-sqlite": "^13.0.0",
  "openai": "^4.0.0",
  "react-native-vector-icons": "^10.0.0",
  "@react-native-async-storage/async-storage": "^1.21.0",
  "@supabase/supabase-js": "^2.43.0",
  "expo-auth-session": "^5.4.0",
  "expo-crypto": "^12.8.0"
}
```

### Development Dependencies
```json
{
  "typescript": "^5.0.0",
  "@types/react": "^18.0.0",
  "@types/react-native": "^0.73.0",
  "eslint": "^8.0.0",
  "prettier": "^3.0.0"
}
```

## 🧪 Testing Strategy

### Unit Testing
- Component testing with React Native Testing Library
- Service layer testing
- Database operations testing
- AI integration testing

### Integration Testing
- Cross-platform compatibility testing
- Storage layer testing
- API integration testing
- End-to-end user flow testing

### Platform-Specific Testing
- Android share intent testing
- Web PWA functionality testing
- Performance testing on both platforms

## 📊 Success Metrics

### Functionality
- [ ] Link capture works from Android share menu
- [ ] AI summarization generates meaningful content
- [ ] Semantic search returns relevant results
- [ ] Chat interface provides helpful responses
- [ ] Cross-platform compatibility maintained
- [ ] **Cloud sync works seamlessly across devices**
- [ ] **Offline functionality maintained**
- [ ] **User authentication secure and reliable**

### Performance
- [ ] App launch time < 3 seconds
- [ ] Search response time < 1 second
- [ ] Smooth scrolling with 100+ notes
- [ ] Efficient memory usage
- [ ] **Sync operations complete within 5 seconds**
- [ ] **Background sync doesn't impact app performance**

### User Experience
- [ ] Intuitive navigation flow
- [ ] Responsive UI across screen sizes
- [ ] Consistent design language
- [ ] Accessibility compliance

## 🚨 Risk Mitigation

### Technical Risks
- **OpenAI API dependency**: Implement fallback mechanisms and rate limiting
- **Cross-platform compatibility**: Regular testing on both platforms
- **Performance with large datasets**: Implement pagination and lazy loading
- **Storage limitations**: Monitor database size and implement cleanup

### Development Risks
- **Scope creep**: Strict adherence to MVP features
- **Timeline delays**: Buffer time in each phase
- **Quality issues**: Regular code reviews and testing

## 📚 Documentation Requirements

- [ ] API documentation
- [ ] Component library documentation
- [ ] Database schema documentation
- [ ] Deployment guide
- [ ] User manual

## 🎉 Deliverables

### MVP Release
- Fully functional Android app
- Web PWA version
- Core AI features working
- Comprehensive testing completed
- Documentation ready

### Future Enhancements (Post-MVP)
- Cloud sync functionality
- Multi-device support
- Offline AI capabilities
- Advanced tag management
- Social sharing features

---

**Total Estimated Timeline:** 16 weeks (with cloud sync)
**Team Size:** 1-2 developers
**Technology Stack:** React Native + Expo + OpenAI API
**Target Platforms:** Android (primary) + Web (PWA)
