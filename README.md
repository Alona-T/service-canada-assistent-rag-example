# Service Canada Assistant

A small retrieval-augmented generation (RAG) example. It crawls a sample of English pages on [canada.ca](https://www.canada.ca/en.html), stores them in a local vector database, and answers questions in a chat page using only that stored text.

The chat is a Service Canada assistant. If the indexed pages do not contain the answer, it says it does not know.

## How it works

1. **Crawl.** `rag_data.py` starts at `https://www.canada.ca/en.html` and follows links inside each page’s `<main>` content. It stays on `www.canada.ca`, keeps only English paths (`/en/`), and skips search pages and PDFs. It stops at 50 pages and waits one second between requests.
2. **Split.** Each page’s main text is cut into chunks of about 1,000 characters, with 200 characters of overlap, so a question can match a short passage instead of a whole page.
3. **Embed and store.** Chunks are embedded with Voyage AI (`voyage-3-large`) and saved in a local Chroma database at `chroma_db/`, in the collection `rag_data`. Chunks are sent a few at a time so the request stays inside Voyage’s free-tier limit.
4. **Answer.** When you ask a question, `query_rag.py` embeds it, retrieves the three closest chunks, and sends those chunks plus your question to Claude (`claude-sonnet-5-5`). The model is instructed to use only that text.

```
canada.ca pages → chunks → Voyage embeddings → Chroma
                                                      ↓
you type a question → nearest chunks → Claude → answer in the chat
```

## Chat

`app.py` serves the page and a single API:

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/` | Chat page (`static/index.html`) |
| POST | `/ask` | Body `{"question": "..."}`. Returns `{"answer": "..."}`. Questions must be 1–2000 characters. |

The page is only bound to your machine, at [http://127.0.0.1:8765](http://127.0.0.1:8765). Suggested questions on the welcome screen are sent the same way as anything you type.

You can also ask from the terminal, without the page:

```bash
python query_rag.py
```

That runs one sample question: “Does Canada offer EI benefits?”

## Setup

Python 3.12 and two API keys are required:

- `VOYAGE_API_KEY` from [Voyage AI](https://www.voyageai.com/) — embeddings while indexing and while answering
- `ANTHROPIC_API_KEY` from [Anthropic](https://console.anthropic.com/) — the chat model

`.env.example` lists the variable names with no values. Copy it and fill in your keys:

```bash
cp .env.example .env
```

Install the libraries and create the index. Indexing crawls the site, so it takes a few minutes.

```bash
python3 -m venv venv
source venv/bin/activate
pip install langchain-community langchain-text-splitters langchain-voyageai langchain-anthropic chromadb beautifulsoup4 requests python-dotenv
python rag_data.py
```

`chroma_db/` is created beside the scripts. Run `rag_data.py` again only when you want to rebuild the index. Running it again adds another copy of the same chunks.

## Run the chat

```bash
source venv/bin/activate
python app.py
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765), type a question, and press Ask. Answers come from the pages already in `chroma_db/`. The assistant does not look up canada.ca at question time.

## Project files

| File | Role |
| --- | --- |
| `rag_data.py` | Crawl canada.ca, chunk the pages, embed them, and write Chroma |
| `query_rag.py` | Retrieve three chunks and ask Claude for an answer |
| `app.py` | Local web server for the chat |
| `static/index.html` | Chat page |
| `chroma_db/` | Stored embeddings (created by `rag_data.py`) |
| `.env.example` | Variable names only, safe to commit |
| `.env` | Your API keys (gitignored) |

## Limits

The index is a sample, not the full Service Canada site: at most 50 English HTML pages reached by walking links from the canada.ca homepage. French pages, PDFs, and anything the crawl never reaches are absent, so the assistant will say it does not know. Answers can also be wrong if the retrieved chunks are related but do not actually contain the fact you asked for.
