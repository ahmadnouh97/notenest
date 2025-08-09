## **Updated Tech Stack for Single Codebase**

### Frontend

* **React Native** with **React Native Web**
* **Expo** for development, builds, and deployment
* **TypeScript** for shared types across platforms
* Component library compatible with both (e.g., **Tamágui**, **Dripsy**, or plain RN styles)

### Storage

* **SQLite** (via `expo-sqlite` on Android)
* **IndexedDB** (via `expo-sqlite` web shim or a polyfill like `react-native-async-storage` web adapter)
* Create a **storage abstraction layer** so both platforms use the same API

### AI

* OpenAI API (gpt-4o-mini for summaries/rephrasing, text-embedding-3-small for vectors)

### Search

* Cosine similarity implemented in JavaScript
* On web: run in memory or IndexedDB
* On Android: run via SQLite

### OS Target

* **Android**
* **Web** (PWA-ready so it can be installed like an app on desktop/mobile browsers)