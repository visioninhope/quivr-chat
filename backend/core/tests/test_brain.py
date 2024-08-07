from uuid import uuid4

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from quivr_core.brain import Brain
from quivr_core.chat import ChatHistory
from quivr_core.llm import LLMEndpoint
from quivr_core.storage.local_storage import TransparentStorage


def test_brain_empty_files():
    # Testing no files
    with pytest.raises(ValueError):
        Brain.from_files(name="test_brain", file_paths=[])


def test_brain_from_files_success(fake_llm: LLMEndpoint, embedder, temp_data_file):
    brain = Brain.from_files(
        name="test_brain", file_paths=[temp_data_file], embedder=embedder, llm=fake_llm
    )
    assert brain.name == "test_brain"
    assert len(brain.chat_history) == 0
    assert brain.llm == fake_llm
    assert brain.vector_db.embeddings == embedder
    assert isinstance(brain.default_chat, ChatHistory)
    assert len(brain.default_chat) == 0

    # storage
    assert isinstance(brain.storage, TransparentStorage)
    assert len(brain.storage.get_files()) == 1


@pytest.mark.asyncio
async def test_brain_from_langchain_docs(embedder):
    chunk = Document("content_1", metadata={"id": uuid4()})
    brain = await Brain.afrom_langchain_documents(
        name="test", langchain_documents=[chunk], embedder=embedder
    )
    # No appended files
    assert len(brain.storage.get_files()) == 0
    assert len(brain.chat_history) == 0


@pytest.mark.asyncio
async def test_brain_search(
    embedder: Embeddings,
):
    chunk1 = Document("content_1", metadata={"id": uuid4()})
    chunk2 = Document("content_2", metadata={"id": uuid4()})
    brain = await Brain.afrom_langchain_documents(
        name="test", langchain_documents=[chunk1, chunk2], embedder=embedder
    )

    k = 2
    result = await brain.asearch("content_1", n_results=k)

    assert len(result) == k
    assert result[0].chunk == chunk1
    assert result[1].chunk == chunk2
    assert result[0].distance == 0
    assert result[1].distance > result[0].distance


@pytest.mark.asyncio
async def test_brain_get_history(
    fake_llm: LLMEndpoint, embedder, temp_data_file, answers
):
    brain = await Brain.afrom_files(
        name="test_brain", file_paths=[temp_data_file], embedder=embedder, llm=fake_llm
    )

    brain.ask("question")
    brain.ask("question")

    assert len(brain.default_chat) == 4


@pytest.mark.asyncio
async def test_brain_ask_streaming(
    fake_llm: LLMEndpoint, embedder, temp_data_file, answers
):
    brain = await Brain.afrom_files(
        name="test_brain", file_paths=[temp_data_file], embedder=embedder, llm=fake_llm
    )

    response = ""
    async for chunk in brain.ask_streaming("question"):
        response += chunk.answer

    assert response == answers[1]
