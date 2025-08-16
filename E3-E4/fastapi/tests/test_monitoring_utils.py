import asyncio

import pytest

import app
import monitoring_utils as mu

openai_requests_total = app.openai_requests_total
openai_request_tokens = app.openai_request_tokens
openai_response_tokens = app.openai_response_tokens
faiss_search_results_count = app.faiss_search_results_count
chatbot_conversations_total = app.chatbot_conversations_total
chatbot_messages_total = app.chatbot_messages_total

monitor_openai_call = mu.monitor_openai_call
monitor_faiss_search = mu.monitor_faiss_search
track_conversation_status = mu.track_conversation_status
track_message_type = mu.track_message_type
OpenAIMonitor = mu.OpenAIMonitor
FAISSMonitor = mu.FAISSMonitor
get_monitoring_stats = mu.get_monitoring_stats


# ---------------------- MONITORING UTILITIES ----------------------

def test_monitor_openai_call_success():
    class Result:
        class Usage:
            prompt_tokens = 2
            completion_tokens = 3
        usage = Usage()

    @monitor_openai_call(model="gpt-test", endpoint="chat/completions")
    async def dummy():
        return Result()

    base_total = openai_requests_total.labels(model="gpt-test", endpoint="chat/completions", status="success")._value.get()
    base_prompt = openai_request_tokens.labels(model="gpt-test", endpoint="chat/completions")._value.get()
    base_completion = openai_response_tokens.labels(model="gpt-test", endpoint="chat/completions")._value.get()

    res = asyncio.run(dummy())
    assert isinstance(res, Result)
    assert openai_requests_total.labels(model="gpt-test", endpoint="chat/completions", status="success")._value.get() == base_total + 1
    assert openai_request_tokens.labels(model="gpt-test", endpoint="chat/completions")._value.get() == base_prompt + 2
    assert openai_response_tokens.labels(model="gpt-test", endpoint="chat/completions")._value.get() == base_completion + 3


def test_monitor_openai_call_error():
    @monitor_openai_call(model="gpt-test", endpoint="chat/completions")
    async def dummy():
        raise ValueError("boom")

    base_err = openai_requests_total.labels(model="gpt-test", endpoint="chat/completions", status="error")._value.get()
    with pytest.raises(ValueError):
        asyncio.run(dummy())
    assert openai_requests_total.labels(model="gpt-test", endpoint="chat/completions", status="error")._value.get() == base_err + 1


def test_monitor_faiss_search_success():
    @monitor_faiss_search(operation="search")
    def dummy():
        return [1, 2, 3]

    base = faiss_search_results_count.labels(operation="search")._value.get()
    res = dummy()
    assert res == [1, 2, 3]
    assert faiss_search_results_count.labels(operation="search")._value.get() == base + 3


def test_monitor_faiss_search_error():
    @monitor_faiss_search(operation="search")
    def dummy():
        raise RuntimeError("fail")

    with pytest.raises(RuntimeError):
        dummy()


def test_tracking_helpers():
    base_status = chatbot_conversations_total.labels(status="nouveau")._value.get()
    track_conversation_status("nouveau")
    assert chatbot_conversations_total.labels(status="nouveau")._value.get() == base_status + 1

    base_type = chatbot_messages_total.labels(type="user")._value.get()
    track_message_type("user")
    assert chatbot_messages_total.labels(type="user")._value.get() == base_type + 1


def test_openai_monitor_contexts():
    base = openai_requests_total.labels(model="gpt-4o-mini", endpoint="chat/completions", status="success")._value.get()
    with OpenAIMonitor(model="gpt-4o-mini"):
        pass
    assert openai_requests_total.labels(model="gpt-4o-mini", endpoint="chat/completions", status="success")._value.get() == base + 1

    base_err = openai_requests_total.labels(model="gpt-4o-mini", endpoint="chat/completions", status="error")._value.get()
    with pytest.raises(RuntimeError):
        with OpenAIMonitor(model="gpt-4o-mini"):
            raise RuntimeError("oops")
    assert openai_requests_total.labels(model="gpt-4o-mini", endpoint="chat/completions", status="error")._value.get() == base_err + 1


def test_faiss_monitor_contexts():
    with FAISSMonitor(operation="similarity_search"):
        pass
    with pytest.raises(ValueError):
        with FAISSMonitor(operation="similarity_search"):
            raise ValueError("bad")


def test_get_monitoring_stats():
    class Dummy:
        def __init__(self, value=0):
            self.value = value
        def sum(self):
            return self.value

    # Patch metrics to provide _value with sum()
    for metric in [openai_requests_total, faiss_search_results_count, chatbot_conversations_total, chatbot_messages_total]:
        metric._value = Dummy()

    stats = get_monitoring_stats()
    assert {"openai_requests_total", "faiss_searches_total", "chatbot_conversations_total", "chatbot_messages_total"} <= stats.keys()
