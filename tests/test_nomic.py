"""Tests for the Nomic model without live API requests."""

import asyncio
import json
import ssl
import sys
from pathlib import Path

import httpx
import pytest

from tekstherkenning_ark.models import nomic as nomic_module
from tekstherkenning_ark.models.nomic import Nomic, NomicWorkflowFailed

ENDPOINT = "https://test.nomic.ai"
PROJECT_ID = "project-1"
WF1_ID = "wf1"
FILENAME = "HEG0801_Houtmonstername&VisueleInspectie.pdf"
SIGNED_URL = "https://storage.example/export.csv"


@pytest.fixture(autouse=True)
def nomic_environment(monkeypatch):
    """Set the Nomic environment variables and disable polling delays."""
    monkeypatch.setenv("NOMIC_ENDPOINT", ENDPOINT)
    monkeypatch.setenv("NOMIC_API_KEY", "npk_test")
    monkeypatch.setenv("NOMIC_PROJECT_ID", PROJECT_ID)
    monkeypatch.setenv("NOMIC_EXTRACT_WF_ID", WF1_ID)

    async def skip_wait(seconds):
        return None

    monkeypatch.setattr(nomic_module, "_wait", skip_wait)


def create_nomic_api(
    search_results=None, agent_status="finished", workflow_definition_status=200, rate_limit_on_search=False
):
    """Create a mock Nomic transport and a list of received requests."""
    requests: list[httpx.Request] = []
    status_polls = iter(["running", agent_status])
    rate_limit = {"active": rate_limit_on_search}

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path

        if str(request.url) == SIGNED_URL:
            return httpx.Response(200, content=b"paal_nummer;diameter\nP1;250\n")
        if path == "/api/v0/files/search":
            if rate_limit["active"]:
                rate_limit["active"] = False
                return httpx.Response(429, headers={"Retry-After": "1"}, json={"error": "rate limit reached"})
            data = search_results if search_results is not None else [{"id": "file-1", "name": FILENAME}]
            return httpx.Response(200, json={"data": data, "nextCursor": None})
        if path == "/api/v0/workflows":
            workflow = {
                "id": WF1_ID,
                "name": "ARK WF1 – Extract duikrapport",
                "requestedFiles": [{"name": "rapport", "optional": False, "multiple": False}],
            }
            return httpx.Response(200, json={"data": [workflow], "nextCursor": None})
        if path == f"/api/v0/workflows/{WF1_ID}":
            if workflow_definition_status == 403:
                return httpx.Response(403, json={"error": "access denied", "code": "forbidden"})
            version = {"id": "version-3", "version": 3, "instructionMarkdown": "Extract tables", "mode": "high"}
            return httpx.Response(200, json={"data": {"id": WF1_ID, "version": version}})
        if path == "/api/v0/agents" and request.method == "POST":
            return httpx.Response(201, json={"data": {"id": "agent-1", "status": "waiting"}})
        if path == "/api/v0/agents/agent-1":
            status = next(status_polls)
            artifacts = [
                {"id": "table-1", "name": "Palen", "type": "TABLE"},
                {"id": "doc-1", "name": "Summary", "type": "MARKDOWN_DOCUMENT"},
            ]
            data = {"id": "agent-1", "status": status, "model": "claude-sonnet-5-5", "artifacts": artifacts}
            return httpx.Response(200, json={"data": data})
        if path == "/api/v0/agents/agent-1/artifacts/table-1/exports":
            return httpx.Response(200, json={"data": {"url": SIGNED_URL}})
        if path == "/api/v0/agents/agent-1/conversation":
            messages = [{"type": "user", "text": "Process the report"}, {"type": "assistant", "text": "Done"}]
            return httpx.Response(200, json={"data": {"messages": messages}})
        if path == "/api/v0/agents/agent-1/usage":
            spend = [
                {"model": "claude-sonnet-5-5", "costUsd": 1.5, "inputTokens": 100, "outputTokens": 10},
                {"model": "claude-haiku-5-5", "costUsd": 0.25, "inputTokens": 50, "outputTokens": 5},
            ]
            return httpx.Response(200, json={"data": {"spend": spend}})
        return httpx.Response(404, json={"error": f"unknown path {path}"})

    return httpx.MockTransport(handler), requests


def run_from_parsed_pdf(transport: httpx.MockTransport, output_dir: Path) -> Nomic:
    """Run ``Nomic.from_parsed_pdf`` against the mock API."""

    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            return await Nomic.from_parsed_pdf(filename=FILENAME, output_dir=output_dir, client=client)

    return asyncio.run(run())


def test_default_client_uses_verified_windows_certificates(tmp_path, monkeypatch):
    transport, _ = create_nomic_api()
    original_client = httpx.AsyncClient
    created_clients = []
    certificate_settings = []

    def create_client(**kwargs):
        certificate_settings.append(kwargs.get("verify"))
        client = original_client(transport=transport, **kwargs)
        created_clients.append(client)
        return client

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(nomic_module.httpx, "AsyncClient", create_client)

    asyncio.run(Nomic.from_parsed_pdf(FILENAME, output_dir=tmp_path))

    context = certificate_settings[0]
    assert isinstance(context, ssl.SSLContext)
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname
    assert created_clients[0].is_closed


def test_successful_run_saves_csv_and_metadata_in_expected_folder(tmp_path):
    transport, _ = create_nomic_api()

    nomic = run_from_parsed_pdf(transport, tmp_path)

    assert nomic.output_folder.parent == tmp_path
    assert nomic.output_folder.name.endswith("-WF1-HEG0801_Houtmonstern")
    assert [path.name for path in nomic.csv_paths] == ["Palen.csv"]
    assert nomic.csv_paths[0].read_bytes() == b"paal_nummer;diameter\nP1;250\n"
    metadata = json.loads((nomic.output_folder / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["agent_id"] == "agent-1"
    assert metadata["filename"] == FILENAME
    assert metadata["total_cost_usd"] == pytest.approx(1.75)
    assert metadata["messages"][0]["text"] == "Process the report"
    assert metadata["artifacts"][0]["name"] == "Palen"


def test_metadata_includes_model_costs_prompt_and_workflow_definition(tmp_path):
    transport, requests = create_nomic_api()

    nomic = run_from_parsed_pdf(transport, tmp_path)

    assert nomic.model == "claude-sonnet-5-5"
    assert nomic.total_cost_usd == pytest.approx(1.75)
    assert nomic.total_input_tokens == 150
    assert nomic.prompt == "Process the report"
    assert nomic.workflow_version == 3
    assert nomic.workflow_inputs == {"rapport": "file-1"}
    launch = next(r for r in requests if r.method == "POST")
    assert json.loads(launch.content)["workflowInputs"] == {"rapport": "file-1"}


def test_signed_url_is_downloaded_without_api_key(tmp_path):
    transport, requests = create_nomic_api()

    run_from_parsed_pdf(transport, tmp_path)

    download = next(r for r in requests if str(r.url) == SIGNED_URL)
    assert "authorization" not in download.headers


@pytest.mark.parametrize(
    "search_results, expected_error",
    [
        ([], FileNotFoundError),
        ([{"id": "a", "name": f"copy_{FILENAME}"}], FileNotFoundError),
        ([{"id": "a", "name": FILENAME}, {"id": "b", "name": FILENAME}], ValueError),
    ],
)
def test_filename_must_have_exactly_one_match(tmp_path, search_results, expected_error):
    transport, _ = create_nomic_api(search_results=search_results)

    with pytest.raises(expected_error):
        run_from_parsed_pdf(transport, tmp_path)


def test_failed_workflow_saves_metadata_and_raises_error(tmp_path):
    transport, _ = create_nomic_api(agent_status="failed")

    with pytest.raises(NomicWorkflowFailed):
        run_from_parsed_pdf(transport, tmp_path)

    metadata_paths = list(tmp_path.glob("*/metadata.json"))
    assert len(metadata_paths) == 1
    assert json.loads(metadata_paths[0].read_text(encoding="utf-8"))["status"] == "failed"
    assert not list(tmp_path.glob("*/*.csv"))


def test_rate_limited_request_is_retried(tmp_path):
    transport, requests = create_nomic_api(rate_limit_on_search=True)

    run_from_parsed_pdf(transport, tmp_path)

    search_requests = [request for request in requests if request.url.path == "/api/v0/files/search"]
    assert len(search_requests) == 2


def test_workflow_definition_is_skipped_without_edit_access(tmp_path):
    transport, _ = create_nomic_api(workflow_definition_status=403)

    nomic = run_from_parsed_pdf(transport, tmp_path)

    assert nomic.workflow_instructions is None
    assert nomic.csv_paths


def test_invalid_endpoint_raises_error(tmp_path, monkeypatch):
    monkeypatch.setenv("NOMIC_ENDPOINT", "https://untrusted.example.com")
    transport, requests = create_nomic_api()

    with pytest.raises(ValueError, match="NOMIC_ENDPOINT"):
        run_from_parsed_pdf(transport, tmp_path)
    assert requests == []


@pytest.mark.parametrize("entrypoint, argument", [("from_pdf", Path("report.pdf")), ("from_rak_id", "HEG0801")])
def test_placeholders_are_not_implemented(entrypoint, argument):
    with pytest.raises(NotImplementedError):
        asyncio.run(getattr(Nomic, entrypoint)(argument))
