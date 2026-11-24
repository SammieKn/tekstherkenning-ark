---
name: nomic-agent-api
description: Integrate with the Nomic Agent API over HTTP (launch, poll, follow-ups, files, images, workflows).
---

# Nomic Agent API quick start

This guide is a **minimal, language-agnostic** path for calling Nomic **background agents** over HTTP from your own app, worker, job runner, or webhook handler.

For full request/response details, error codes, and workflow shapes, see the [Agent API](https://docs.nomic.ai/api/agents) reference. For limits and `429` behavior, see [Rate limits](https://docs.nomic.ai/api/rate-limits).

## What you are integrating

Background agents are **asynchronous**. You **create** a run, **poll** until the status is terminal, then read **conversation** text and/or **artifacts**. Optional **follow-ups** reuse the same agent id for the next turn (multi-turn “sessions” in your product map to **one agent id** plus follow-up calls).

## Prerequisites

1. **Base URL** — `https://<your-domain>.nomic.ai/api/v0` (same pattern as the rest of the Platform API; see [Overview](https://docs.nomic.ai/api/overview)).
2. **API key** — Bearer token with the **`developer`** scope, created in the Developer Console on the instance you call.
3. **HTTP client** — anything that can send `Authorization`, `Content-Type: application/json`, and multipart file uploads.

## Minimal happy path (simple agent)

### 1. Launch

`POST /api/v0/agents` with a JSON body:

```json
{
  "prompt": {
    "text": "Your instruction for this run."
  }
}
```

Optional: `prompt.images` (inline image context), `fileIds` (array of file UUIDs the agent may read), `projectId`, `model` (`auto` or a concrete model such as `claude-sonnet-5-5`), and `mode` (`low`, `medium`, `high`, or `xhigh`). Omit `workflowId` for a **simple** text-driven agent.

The response is **`201 Created`** with a `data` object. Save **`data.id`** (agent id), note **`data.status`** (usually `waiting` or `running`), and read **`data.model`** if you need the resolved concrete model for the run.

### 2. Poll until finished (or failed / stopped)

`GET /api/v0/agents/{id}` in a loop. Active statuses include `waiting`, `running`, and `awaiting_tool`; keep polling until `data.status` is one of:

- `finished` — success; inspect `data.artifacts` and/or conversation (below).
- `failed` — inspect error context in the conversation if needed.
- `stopped` — user or integration cancelled; you can still [follow up](https://docs.nomic.ai/api/agents#add-follow-up) if that fits your product.

Use **exponential backoff** with a cap (for example start at 2s, double toward a 30s max, add small jitter). Respect **`429`** responses: sleep for the **`Retry-After`** header (seconds), then retry the same request.

### 3. Read the result

Two common options:

- **Conversation (agent text)** — `GET /api/v0/agents/{id}/conversation` returns a linear `messages` list. For “final answer” style UIs, take the `assistant` messages after the **last** `user` message; trailing rows may include tool or error entries, so do not assume the last message is always `assistant`.
- **Artifacts** — when `status` is `finished`, `GET /api/v0/agents/{id}` includes `artifacts` metadata. Fetch content with `GET /api/v0/agents/{id}/artifacts/{artifactId}` for each artifact you need (markdown documents, tables, etc.).

## Follow-ups (same agent, new instruction)

When the agent is in a **terminal** state (`finished`, `failed`, or `stopped`), send:

`POST /api/v0/agents/{id}/followup` with `{ "prompt": { "text": "…" } }`. You may include `prompt.images` on a follow-up using the same shape and limits as launch.

**Important — polling race:** the follow-up response is **`202 Accepted`** and returns current agent `data`. The platform starts the new turn asynchronously. Right after follow-up, **`GET /api/v0/agents/{id}` may still show `status: "finished"`** from the _previous_ turn for a short time. Before you treat `finished` as “done for this turn,” either:

- poll until status becomes **`running`**, **`waiting`**, or **`awaiting_tool`**, then poll until terminal again; or
- apply a short “kick” loop: if you just posted a follow-up and status is still `finished`, keep polling sub-second for a bounded window (tens of seconds) until it leaves `finished`, then run your normal terminal poll.

Without this, you can read the **old** conversation and show stale text to users.

## Discover projects

`GET /api/v0/projects` returns projects the authenticated user can access. Each project object includes `id`, `name`, `description`, `createdAt`, and `updatedAt`. Use the project `id` as `projectId` when listing workflows (`GET /api/v0/workflows?projectId=…`) or launching an agent.

## Discover workflows

`GET /api/v0/workflows` returns available workflows on the instance. Each workflow object includes an `id`, `name`, `description`, and a `requestedFiles` array describing its file-input slots (name, description, optional, multiple). Use the workflow `id` as `workflowId` when launching an agent. Optional `projectId` filters to workflows in a project.

## Find and attach files

Two ways to obtain file UUIDs:

1. **Search existing files** — `GET /api/v0/files/search?query=<name>&limit=10` returns files matching the name. Each result includes `id`, `name`, and `path`.
2. **Upload a new file** — `POST /api/v0/files/upload` as **multipart** form field `file` (filename + bytes + content type).

Use the file **`id`** (UUID string) in **`fileIds`** on `POST /api/v0/agents` (simple agents) or in **`workflowInputs`** (workflow agents with file-input slots).

Follow-up requests do not accept `fileIds`. If you need new files mid-session, launch a new agent.

## Attach images to prompts

For visual context that does not need to become a persisted Nomic file, include up to 4 inline images on `prompt.images` when launching a simple agent, launching a prompt-driven workflow, or sending a follow-up:

```json
{
  "prompt": {
    "text": "Review this site photo and list visible safety issues.",
    "images": [
      {
        "media_type": "image/jpeg",
        "data": "<base64-encoded-image-bytes>"
      }
    ]
  }
}
```

Supported media types are `image/jpeg`, `image/png`, `image/webp`, and `image/gif`. Each image can be up to 20 MB after base64 decoding. Use raw base64 image bytes in `data`, not a `data:` URL. Because images are part of `prompt`, they cannot be used with workflows that declare file-input slots and therefore require `workflowInputs` instead of `prompt`.

## Workflow agents (one-liner)

Pass **`workflowId`** instead of a bare prompt-only simple agent:

- **Prompt-driven workflows** — same `prompt.text` and optional `prompt.images` as simple agents.
- **File-slot workflows** — send **`workflowInputs`**: a map of slot name → value where single-file slots use a UUID string, multi-file slots use an array of UUID strings, and optional unset slots use explicit `null` (see [Agent API](https://docs.nomic.ai/api/agents) examples).

Workflow agents use the workflow-configured model and effort by default. Include `model` or `mode` on launch to override for that run only. Former `mode` values: `standard` maps to `low`; `deep_research` maps to `medium`; `background_agent` maps to `high`.

Do not mix simple-agent-only fields with incompatible workflow combinations; the server returns **`400`** for invalid pairs.

## Idempotency and “one session” in your app

Map your domain’s “thread” or “ticket” to **one Nomic agent id** when you want continuity:

- First message → **`POST /api/v0/agents`**.
- Later messages → **`POST …/followup`** on that id **only after** the prior turn reached a terminal state (or after you **`POST …/stop`** if you need to interrupt).

If a stored agent id 404s (deleted), fall back to a fresh launch.

## Operational checklist

| Topic                   | Recommendation                                                                                            |
| ----------------------- | --------------------------------------------------------------------------------------------------------- |
| Auth                    | `Authorization: Bearer <npk_…>` on every call                                                             |
| Launch / follow-up rate | **Heavy** tier (see [Agent API](https://docs.nomic.ai/api/agents) per-endpoint table); space out launches |
| Polling                 | Backoff + jitter; avoid tight loops                                                                       |
| `429`                   | Honor **`Retry-After`**                                                                                   |
| UI deep link            | `{origin}/assistant/{agentId}` is a typical link to open the agent in the Platform UI                     |

## Next steps

- Read the full **[Agent API](https://docs.nomic.ai/api/agents)** (lifecycle diagram, stop/delete, error codes).
- Confirm **[Rate limits](https://docs.nomic.ai/api/rate-limits)** against your expected volume.

---

_This page is the fastest path from zero to a working agent integration; keep the detailed reference open in a second tab while you code._
