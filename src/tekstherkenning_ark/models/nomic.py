"""Run Nomic WF1 workflows and save CSV results and run metadata.

The input report must already be available in Nomic. Importing the exported CSVs into the
other domain models is outside this model's responsibility.
"""

from __future__ import annotations

import asyncio
import os
import random
import re
import ssl
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, computed_field

from tekstherkenning_ark import constants
from tekstherkenning_ark.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

TERMINAL_STATUSES = {"finished", "failed", "stopped"}
WF1_LABEL = "WF1"
MAX_RATE_LIMIT_ATTEMPTS = 5
_ENDPOINT_PATTERN = re.compile(r"^https://[A-Za-z0-9.-]+\.nomic\.ai$")
_INVALID_PATH_CHARACTERS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class NomicError(Exception):
    """An error returned by the Nomic API.

    Parameters
    ----------
    message : str
        Error description.
    status_code : int | None
        HTTP status code, if available.
    code : str | None
        Nomic error code, if available.
    """

    def __init__(self, message: str, status_code: int | None = None, code: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class NomicWorkflowFailed(RuntimeError):
    """The Nomic workflow ended with status ``failed`` or ``stopped``."""


@dataclass(frozen=True)
class _NomicConfig:
    """Nomic API configuration loaded from environment variables."""

    endpoint: str
    api_key: str
    project_id: str
    extract_workflow_id: str

    @classmethod
    def from_environment(cls) -> _NomicConfig:
        """Load and validate the Nomic environment configuration.

        Returns
        -------
        _NomicConfig
            Validated configuration.

        Raises
        ------
        ValueError
            If a variable is missing or the endpoint is not a valid Nomic HTTPS host.
        """
        names = {
            "endpoint": "NOMIC_ENDPOINT",
            "api_key": "NOMIC_API_KEY",
            "project_id": "NOMIC_PROJECT_ID",
            "extract_workflow_id": "NOMIC_EXTRACT_WF_ID",
        }
        values = {field: (os.getenv(name) or "").strip() for field, name in names.items()}
        missing = [names[field] for field, value in values.items() if not value]
        if missing:
            raise ValueError(f"Missing Nomic environment variables: {', '.join(missing)}")

        values["endpoint"] = values["endpoint"].rstrip("/")
        if not _ENDPOINT_PATTERN.match(values["endpoint"]):
            raise ValueError("NOMIC_ENDPOINT must be an HTTPS URL on a *.nomic.ai domain")

        return cls(**values)


async def _wait(seconds: float) -> None:
    """Wait for the specified number of seconds."""
    await asyncio.sleep(seconds)


class _NomicClient:
    """Async wrapper around the Nomic Platform API (``/api/v0``).

    Parameters
    ----------
    config : _NomicConfig
        Configuration containing the endpoint and API key.
    http_client : httpx.AsyncClient
        HTTP client. The API key is sent per API request, so signed URL downloads
        do not receive an Authorization header.
    """

    def __init__(self, config: _NomicConfig, http_client: httpx.AsyncClient) -> None:
        self._base_url = f"{config.endpoint}/api/v0"
        self._headers = {"Authorization": f"Bearer {config.api_key}", "Accept": "application/json"}
        self._http = http_client

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Send an API request, handling rate limits and API errors."""
        url = f"{self._base_url}{path}"
        for attempt in range(1, MAX_RATE_LIMIT_ATTEMPTS + 1):
            response = await self._http.request(method, url, headers=self._headers, **kwargs)
            if response.status_code == 429 and attempt < MAX_RATE_LIMIT_ATTEMPTS:
                delay = float(response.headers.get("Retry-After", "5"))
                logger.warning(f"Nomic rate limit reached for {method} {path}; retrying in {delay} s")
                await _wait(delay)
                continue
            if response.status_code >= 400:
                code = None
                try:
                    body = response.json()
                    code = body.get("code")
                    message = body.get("error") or response.text
                except ValueError:
                    message = response.text
                raise NomicError(
                    f"Nomic API error for {method} {path} ({response.status_code}): {message}",
                    status_code=response.status_code,
                    code=code,
                )
            return response.json() if response.content else {}
        raise NomicError(f"Nomic rate limit persisted for {method} {path}", status_code=429)

    async def find_file(self, filename: str) -> dict[str, Any]:
        """Find a file by its exact name.

        Parameters
        ----------
        filename : str
            Exact filename in Nomic, including its extension.

        Returns
        -------
        dict[str, Any]
            File details (``id``, ``name``, ``path``, ...).

        Raises
        ------
        FileNotFoundError
            If no file has this exact name.
        ValueError
            If multiple files have this exact name.
        """
        exact_matches: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {"query": filename, "limit": 50}
            if cursor:
                params["cursor"] = cursor
            response = await self._request("GET", "/files/search", params=params)
            exact_matches.extend(file for file in response.get("data", []) if file.get("name") == filename)
            cursor = response.get("nextCursor")
            if not cursor:
                break

        if not exact_matches:
            raise FileNotFoundError(f"No file with the exact name '{filename}' found in Nomic")
        if len(exact_matches) > 1:
            paths = ", ".join(file.get("path", file["id"]) for file in exact_matches)
            raise ValueError(f"Multiple files named '{filename}' found in Nomic: {paths}")
        return exact_matches[0]

    async def get_workflow(self, workflow_id: str, project_id: str) -> dict[str, Any]:
        """Get the workflow name and input slots from the project's workflows."""
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {"projectId": project_id, "limit": 100}
            if cursor:
                params["cursor"] = cursor
            response = await self._request("GET", "/workflows", params=params)
            for workflow in response.get("data", []):
                if workflow.get("id") == workflow_id:
                    return workflow
            cursor = response.get("nextCursor")
            if not cursor:
                raise ValueError(f"Workflow '{workflow_id}' not found in Nomic project '{project_id}'")

    async def get_workflow_definition(self, workflow_id: str) -> dict[str, Any] | None:
        """Get the full workflow definition, or ``None`` without edit access."""
        try:
            response = await self._request("GET", f"/workflows/{workflow_id}")
        except NomicError as error:
            if error.status_code == 403:
                logger.warning("No workflow edit access; workflow definition will not be saved")
                return None
            raise
        return response.get("data")

    async def start_workflow(
        self, workflow_id: str, workflow_inputs: dict[str, str | list[str] | None], project_id: str
    ) -> dict[str, Any]:
        """Start a workflow agent and return its details."""
        body = {"workflowId": workflow_id, "workflowInputs": workflow_inputs, "projectId": project_id}
        response = await self._request("POST", "/agents", json=body)
        return response["data"]

    async def get_agent(self, agent_id: str) -> dict[str, Any]:
        """Get the current agent details."""
        response = await self._request("GET", f"/agents/{agent_id}")
        return response["data"]

    async def wait_for_agent(self, agent_id: str, timeout_s: float) -> dict[str, Any]:
        """Poll an agent until it reaches a terminal status, using exponential backoff.

        Parameters
        ----------
        agent_id : str
            Agent ID.
        timeout_s : float
            Maximum waiting time in seconds.

        Returns
        -------
        dict[str, Any]
            Agent details with a terminal status.

        Raises
        ------
        TimeoutError
            If the agent does not finish within ``timeout_s``.
        """
        deadline = time.monotonic() + timeout_s
        interval = 2.0
        while True:
            agent = await self.get_agent(agent_id)
            if agent.get("status") in TERMINAL_STATUSES:
                return agent
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Nomic agent '{agent_id}' did not finish within {timeout_s} s")
            logger.debug(f"Nomic agent {agent_id} has status '{agent.get('status')}'")
            await _wait(interval + random.uniform(0, 1))
            interval = min(interval * 2, 30.0)

    async def get_conversation(self, agent_id: str) -> list[dict[str, Any]]:
        """Get the agent's user, assistant and error messages."""
        response = await self._request("GET", f"/agents/{agent_id}/conversation")
        return response.get("data", {}).get("messages", [])

    async def get_usage(self, agent_id: str) -> list[dict[str, Any]]:
        """Get token usage and costs per model."""
        response = await self._request("GET", f"/agents/{agent_id}/usage")
        return response.get("data", {}).get("spend", [])

    async def export_table_csv(self, agent_id: str, artifact_id: str) -> bytes:
        """Export a table artifact as CSV and download its contents."""
        response = await self._request(
            "GET", f"/agents/{agent_id}/artifacts/{artifact_id}/exports", params={"format": "csv"}
        )
        download = await self._http.get(response["data"]["url"], follow_redirects=True)
        download.raise_for_status()
        return download.content


class NomicMessage(BaseModel):
    """A message from a Nomic agent conversation.

    Attributes
    ----------
    type : str
        Message type: ``user``, ``assistant`` or ``error``.
    text : str | None
        Message contents.
    created_at : datetime | None
        Message creation time.
    """

    type: str
    text: str | None = None
    created_at: datetime | None = None


class NomicCost(BaseModel):
    """Token usage and costs for one model in a Nomic run.

    Attributes
    ----------
    model : str | None
        Model name.
    cost_usd : float
        Cost in USD.
    input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens : int
        Token counts per category.
    """

    model: str | None = None
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0


class NomicArtifact(BaseModel):
    """An artifact produced by a Nomic agent.

    Attributes
    ----------
    id : str
        Artifact ID.
    name : str
        Artifact name.
    type : str
        Artifact type, for example ``TABLE`` or ``MARKDOWN_DOCUMENT``.
    created_at : datetime | None
        Artifact creation time.
    csv_path : Path | None
        Downloaded CSV path, only for tables.
    """

    id: str
    name: str
    type: str
    created_at: datetime | None = None
    csv_path: Path | None = None


class Nomic(BaseModel):
    """Metadata and results of a Nomic workflow run.

    Instantiate using a classmethod, for example ``await Nomic.from_parsed_pdf("report.pdf")``.

    Attributes
    ----------
    filename : str
        Report filename in Nomic.
    file_id : str
        Report ID in Nomic.
    file_path : str | None
        Report path in Nomic.
    project_id : str
        Nomic project ID.
    workflow_id : str
        Workflow ID.
    workflow_name : str | None
        Workflow name.
    workflow_inputs : dict[str, str | list[str] | None]
        Inputs supplied to the workflow.
    workflow_version_id, workflow_version, workflow_instructions, workflow_mode, workflow_model
        Workflow definition, only available with workflow edit access.
    agent_id : str
        Nomic agent ID.
    status : str
        Final run status.
    model : str | None
        Resolved model used for the run.
    title : str | None
        Run title in Nomic.
    started_at : datetime
        Local time at which the run started.
    finished_at : datetime | None
        Time of the run's last update in Nomic.
    platform_link : str
        Link to the run in Nomic.
    messages : list[NomicMessage]
        Agent conversation.
    costs : list[NomicCost]
        Token usage and costs per model.
    artifacts : list[NomicArtifact]
        Produced artifacts.
    output_folder : Path
        Folder containing the CSVs and ``metadata.json``.
    """

    filename: str
    file_id: str
    file_path: str | None = None
    project_id: str
    workflow_id: str
    workflow_name: str | None = None
    workflow_inputs: dict[str, str | list[str] | None] = {}

    workflow_version_id: str | None = None
    workflow_version: int | None = None
    workflow_instructions: str | None = None
    workflow_mode: str | None = None
    workflow_model: str | None = None

    agent_id: str
    status: str
    model: str | None = None
    title: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    platform_link: str

    messages: list[NomicMessage] = []
    costs: list[NomicCost] = []
    artifacts: list[NomicArtifact] = []
    output_folder: Path

    @computed_field
    @property
    def prompt(self) -> str | None:
        """Return the first user message supplied to the agent."""
        return next((message.text for message in self.messages if message.type == "user"), None)

    @computed_field
    @property
    def total_cost_usd(self) -> float:
        """Return total run costs in USD across all models."""
        return sum(cost.cost_usd for cost in self.costs)

    @computed_field
    @property
    def total_input_tokens(self) -> int:
        """Return the total input token count across all models."""
        return sum(cost.input_tokens for cost in self.costs)

    @computed_field
    @property
    def total_output_tokens(self) -> int:
        """Return the total output token count across all models."""
        return sum(cost.output_tokens for cost in self.costs)

    @computed_field
    @property
    def csv_paths(self) -> list[Path]:
        """Return all downloaded CSV paths."""
        return [artifact.csv_path for artifact in self.artifacts if artifact.csv_path is not None]

    @classmethod
    async def from_parsed_pdf(
        cls,
        filename: str,
        *,
        timeout_s: float = 1800,
        output_dir: Path | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> Nomic:
        """Run WF1 on a report already parsed in Nomic and save the CSVs.

        Parameters
        ----------
        filename : str
            Exact report filename in Nomic, including its extension.
        timeout_s : float, optional
            Maximum workflow waiting time in seconds, default 1800.
        output_dir : Path | None, optional
            Base output directory, default ``constants.NOMIC_DIR``.
        client : httpx.AsyncClient | None, optional
            Optional HTTP client, for example for tests; otherwise one is created.

        Returns
        -------
        Nomic
            Run metadata, including downloaded CSV paths.

        Raises
        ------
        NomicWorkflowFailed
            If the workflow ends with ``failed`` or ``stopped``; metadata is still saved.
        """
        config = _NomicConfig.from_environment()
        owns_client = client is None
        if client is None:
            verify = ssl.create_default_context() if sys.platform == "win32" else True
            http_client = httpx.AsyncClient(timeout=60.0, verify=verify)
        else:
            http_client = client
        try:
            return await cls._run_workflow(
                api=_NomicClient(config, http_client),
                config=config,
                filename=filename,
                timeout_s=timeout_s,
                output_dir=output_dir or constants.NOMIC_DIR,
            )
        finally:
            if owns_client:
                await http_client.aclose()

    @classmethod
    async def from_pdf(cls, pdf_path: Path) -> Nomic:
        """Upload a new PDF to Nomic and run WF1 (not implemented yet)."""
        raise NotImplementedError("Nomic.from_pdf is not implemented yet; use from_parsed_pdf")

    @classmethod
    async def from_rak_id(cls, rak_id: str) -> Nomic:
        """Find a report by rakcode in Nomic and run WF1 (not implemented yet)."""
        raise NotImplementedError("Nomic.from_rak_id is not implemented yet; use from_parsed_pdf")

    @classmethod
    async def _run_workflow(
        cls,
        api: _NomicClient,
        config: _NomicConfig,
        filename: str,
        timeout_s: float,
        output_dir: Path,
    ) -> Nomic:
        """Execute a WF1 run and construct its Nomic model."""
        file = await api.find_file(filename)
        workflow = await api.get_workflow(config.extract_workflow_id, config.project_id)
        workflow_inputs = _build_workflow_inputs(workflow, file["id"])

        started_at = datetime.now()
        logger.info(f"Starting Nomic workflow '{workflow.get('name')}' for '{filename}'")
        agent = await api.start_workflow(config.extract_workflow_id, workflow_inputs, config.project_id)
        agent_id = agent["id"]
        logger.info(f"Nomic agent started: {config.endpoint}/assistant/{agent_id}")
        agent = await api.wait_for_agent(agent_id, timeout_s)

        output_folder = _create_output_folder(output_dir, started_at, filename)
        artifacts = [
            NomicArtifact(
                id=artifact["id"],
                name=artifact.get("name") or artifact["id"],
                type=artifact.get("type", ""),
                created_at=artifact.get("createdAt"),
            )
            for artifact in agent.get("artifacts") or []
        ]
        if agent["status"] == "finished":
            used_names: set[str] = set()
            for artifact in artifacts:
                if artifact.type != "TABLE":
                    continue
                csv_path = output_folder / _unique_csv_name(artifact.name, used_names)
                csv_path.write_bytes(await api.export_table_csv(agent_id, artifact.id))
                artifact.csv_path = csv_path
                logger.info(f"CSV saved: {csv_path}")

        definition = await api.get_workflow_definition(config.extract_workflow_id)
        version = (definition or {}).get("version") or {}

        nomic = cls(
            filename=filename,
            file_id=file["id"],
            file_path=file.get("path"),
            project_id=config.project_id,
            workflow_id=config.extract_workflow_id,
            workflow_name=workflow.get("name"),
            workflow_inputs=workflow_inputs,
            workflow_version_id=version.get("id"),
            workflow_version=version.get("version"),
            workflow_instructions=version.get("instructionMarkdown"),
            workflow_mode=version.get("mode"),
            workflow_model=version.get("model"),
            agent_id=agent_id,
            status=agent["status"],
            model=agent.get("model"),
            title=agent.get("title"),
            started_at=started_at,
            finished_at=agent.get("updatedAt"),
            platform_link=f"{config.endpoint}/assistant/{agent_id}",
            messages=await _fetch_best_effort(api.get_conversation, agent_id, "conversation", _parse_messages),
            costs=await _fetch_best_effort(api.get_usage, agent_id, "costs", _parse_costs),
            artifacts=artifacts,
            output_folder=output_folder,
        )
        nomic.save_metadata()

        if nomic.status != "finished":
            raise NomicWorkflowFailed(
                f"Nomic workflow ended with status '{nomic.status}'; see {nomic.platform_link} "
                f"and {nomic.output_folder / 'metadata.json'}"
            )
        return nomic

    def save_metadata(self) -> Path:
        """Save the run metadata as ``metadata.json`` in the output folder.

        Returns
        -------
        Path
            Path to the saved metadata file.
        """
        self.output_folder.mkdir(parents=True, exist_ok=True)
        metadata_path = self.output_folder / "metadata.json"
        metadata_path.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        logger.info(f"Nomic metadata saved: {metadata_path}")
        return metadata_path


def _build_workflow_inputs(workflow: dict[str, Any], file_id: str) -> dict[str, str | list[str] | None]:
    """Assign the file to the required input slot and set optional slots to ``None``."""
    slots = workflow.get("requestedFiles") or []
    required = [slot for slot in slots if not slot.get("optional")]
    if len(required) != 1:
        raise ValueError(
            f"Workflow '{workflow.get('name')}' has {len(required)} required input slots; expected exactly 1"
        )
    return {
        slot["name"]: ([file_id] if slot.get("multiple") else file_id) if slot in required else None for slot in slots
    }


def _sanitize_name(name: str) -> str:
    """Replace characters that are invalid in Windows filenames."""
    return _INVALID_PATH_CHARACTERS.sub("_", name).strip(" .") or "unknown"


def _create_output_folder(output_dir: Path, started_at: datetime, filename: str) -> Path:
    """Create a timestamped WF1 output folder, adding a suffix if it already exists."""
    base_name = f"{started_at:%y%m%d-%H%M}-{WF1_LABEL}-{_sanitize_name(Path(filename).stem[:20])}"
    output_folder = output_dir / base_name
    index = 2
    while output_folder.exists():
        output_folder = output_dir / f"{base_name}-{index}"
        index += 1
    output_folder.mkdir(parents=True)
    return output_folder


def _unique_csv_name(artifact_name: str, used_names: set[str]) -> str:
    """Return a unique CSV filename based on the artifact name."""
    base = _sanitize_name(artifact_name)
    name = f"{base}.csv"
    index = 2
    while name.lower() in used_names:
        name = f"{base}_{index}.csv"
        index += 1
    used_names.add(name.lower())
    return name


def _parse_messages(messages: list[dict[str, Any]]) -> list[NomicMessage]:
    """Convert Nomic conversation data to ``NomicMessage`` objects."""
    return [
        NomicMessage(type=message.get("type", ""), text=message.get("text"), created_at=message.get("createdAt"))
        for message in messages
    ]


def _parse_costs(spend: list[dict[str, Any]]) -> list[NomicCost]:
    """Convert Nomic usage data to ``NomicCost`` objects."""
    return [
        NomicCost(
            model=usage.get("model"),
            cost_usd=usage.get("costUsd") or 0.0,
            input_tokens=usage.get("inputTokens") or 0,
            output_tokens=usage.get("outputTokens") or 0,
            cache_creation_tokens=usage.get("cacheCreationTokens") or 0,
            cache_read_tokens=usage.get("cacheReadTokens") or 0,
        )
        for usage in spend
    ]


async def _fetch_best_effort(fetch, agent_id: str, description: str, convert) -> list:
    """Fetch additional metadata, logging API errors and returning an empty list."""
    try:
        return convert(await fetch(agent_id))
    except NomicError as error:
        logger.warning(f"Could not fetch Nomic {description}: {error}")
        return []
