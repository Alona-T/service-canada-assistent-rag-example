import os
import time
from urllib.parse import urljoin, urlparse

import bs4
import requests
from dotenv import load_dotenv

load_dotenv()
load_dotenv(".env.example")
os.environ.setdefault("USER_AGENT", "service-canada-assistent-example/1.0")

from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_voyageai import VoyageAIEmbeddings

start = "https://www.canada.ca/en.html"
seen = {start}
queue = [start]
headers = {"User-Agent": os.environ["USER_AGENT"]}

while queue and len(seen) < 50:
    url = queue.pop(0)
    page = requests.get(url, headers=headers, timeout=30)
    soup = bs4.BeautifulSoup(page.text, "html.parser")
    for link in soup.select("main a[href]"):
        next_url = urljoin(url, link["href"].split("#")[0])
        parsed = urlparse(next_url)
        if parsed.netloc != "www.canada.ca" or not parsed.path.startswith("/en/"):
            continue
        if next_url in seen or "/search" in parsed.path or parsed.path.endswith(".pdf"):
            continue
        seen.add(next_url)
        queue.append(next_url)
    time.sleep(1)

web_paths = sorted(seen)
print(f"Found {len(web_paths)} English pages")

bs4_strainer = bs4.SoupStrainer("main")

loader = WebBaseLoader(
    web_paths=web_paths,
    bs_kwargs={"parse_only": bs4_strainer},
)

documents = loader.load()

print(documents)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, add_start_index=True)
all_splits = text_splitter.split_documents(documents)

print(all_splits)

embeddings = VoyageAIEmbeddings(model="voyage-3-large")

vector_store = Chroma(
    collection_name="rag_data",
    embedding_function=embeddings,
    persist_directory="./chroma_db",
)

# Voyage's unpaid limit is 3 requests and 10,000 tokens per minute.
# Send a few chunks at a time so the save is not rejected.
batch_size = 5
added = 0
for start_index in range(0, len(all_splits), batch_size):
    batch = all_splits[start_index:start_index + batch_size]
    ids = vector_store.add_documents(batch)
    added += len(ids)
    print(f"Added {added} of {len(all_splits)} chunks")
    if start_index + batch_size < len(all_splits):
        time.sleep(21)

print(f"Added {added} documents to the vector store")



