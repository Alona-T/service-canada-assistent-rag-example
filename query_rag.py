from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

load_dotenv()
load_dotenv(".env.example")
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_voyageai import VoyageAIEmbeddings

embeddings = VoyageAIEmbeddings(model="voyage-3-large")

vector_store = Chroma(
    collection_name="rag_data",
    embedding_function=embeddings,
    persist_directory="./chroma_db",
)

prompt = ChatPromptTemplate.from_template(
    """You are a warm Service Canada Assistant helping someone who wants a quick answer.
Speak directly to them. Open with a friendly sentence, then give the useful details.
Use only the information below. Never mention the context, the source text, or that information was retrieved.
If the information below does not contain the answer, say "I do not know" and offer to help with another question.
Question: {question}
Information: {context}
Answer:
"""
)

llm = ChatAnthropic(model="claude-sonnet-5-5")


def _message_text(message) -> str:
    content = message.content
    if isinstance(content, str):
        return content.strip()
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(parts).strip()


def answer_question(question: str) -> str:
    retrieved_docs = vector_store.similarity_search(question, k=3)
    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)
    message = prompt.invoke({"question": question, "context": docs_content})
    answer = llm.invoke(message)
    return _message_text(answer) or "I do not know"


if __name__ == "__main__":
    print(answer_question("Does Canada offer EI benefits?"))
