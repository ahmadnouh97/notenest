# 🧭 User Journey – **NoteNest** (Smart Link Brain App)

## **1. Capture a Link**

* User opens any app (browser, YouTube, Twitter, etc.).
* Finds an interesting link.
* Taps **Share** and selects **NoteNest**.

## **2. Receive the Link**

* App gets the URL and optional title from Android’s share intent.

## **3. Generate Initial Summary**

* App sends the URL (and title if available) to the LLM API with a summarization prompt.
* If the LLM can summarize:

  * Returns a short summary + optional suggested tags.
* If not:

  * Returns an empty or placeholder summary.

## **4. Editable Summary Input**

* App opens an **edit screen** with:

  * Input box **pre-filled** with the AI-generated summary (or empty if none).
  * User can:

    * Edit the summary.
    * Add their own notes.
    * Completely rewrite it.

## **5. Optional Rephrase**

* User can tap a **“Rephrase”** button to send the current input text to the LLM.
* LLM returns a polished or clearer version.
* Input box updates with the rephrased text (user can still modify it before saving).

## **6. Save the Note**

* User taps **Save**.
* App stores:

  * URL
  * Title (if available)
  * Final summary/note
  * Tags (AI-suggested or user-added)
  * Date created
* All data is saved in a **local SQLite database** (with optional cloud sync later).

## **7. View & Search Saved Notes**

* Main screen shows a **scrollable list of link cards**:

  * Thumbnail (if available)
  * Title
  * Summary
  * Tags
* **Search Box** at the top:

  * Uses **semantic search** (via locally stored embeddings or LLM API) to find relevant notes based on meaning, not just keywords.
  * Filters the note list in real time.
* User can tap:

  * **Open** → launches original link in browser.
  * **Edit** → update summary/tags.

## **8. Chat With Notes**

* User opens the **Chat tab**.
* Types a query, e.g., *“Show me all notes about fitness.”*
* App:

  * Runs **semantic search** on the local database.
  * Retrieves matching notes.
  * Sends the query + retrieved notes to the LLM.
* LLM responds with:

  * Summarized results.
  * Direct answers.
  * Optional related note suggestions.

## **9. Continuous Knowledge Growth**

* Over time, the database grows with user-curated, AI-enhanced notes.
* The chat feature becomes smarter as more context is available.
