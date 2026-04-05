# Teams Webhook Client

Small Python client for posting messages to a Microsoft Teams channel webhook.

Features:

- Reusable Python class.
- Command-line interface.
- Optional `requests` transport.
- Retry with exponential backoff for `429` and `5xx` responses.
- Installable `teams-post` console command.
- Rich JSON payload input from a file or stdin.
- Structured text or JSON logs for CI.

## Files

- `.env.example`: example webhook environment file.
- `.env`: local webhook environment file created with a placeholder URL.
- `.github/workflows/post-to-teams.yml`: sample GitHub Actions workflow.
- `.gitignore`: local environment and build artifact ignore rules.
- `Makefile`: common setup and run targets.
- `payload.json`: sample full Teams webhook payload.
- `card.json`: sample Adaptive Card payload.
- `tests/test_teams_webhook.py`: smoke tests for payload generation and JSON loading.
- `teams_webhook.py`: reusable client class.
- `example.py`: simple example usage.
- `pyproject.toml`: packaging metadata and `teams-post` entry point.
- `CHAT_TRANSCRIPT.md`: saved project conversation summary.
- `DESIGN_DECISIONS.md`: saved implementation decisions and tradeoffs.

## Make Targets

Common commands:

```bash
make install
make install-requests
make example
make doctor
make test
make post MESSAGE="Hello from make"
make post-json
make post-card
```

The `post`, `post-json`, and `post-card` targets load `TEAMS_WEBHOOK_URL` from `.env` if present, otherwise they use the current shell environment.

Run `make doctor` to verify that `.venv`, `teams-post`, the sample payload files, and `TEAMS_WEBHOOK_URL` are all available before posting.

Create a local `.env` from the example:

```bash
cp .env.example .env
```

This folder now already includes a local `.env` placeholder. Replace the placeholder value with your real webhook URL before posting.

## Usage

Set the webhook URL and run the example:

```bash
export TEAMS_WEBHOOK_URL="https://your-webhook-url"
python example.py
```

Use the built-in CLI:

```bash
export TEAMS_WEBHOOK_URL="https://your-webhook-url"
python teams_webhook.py "Hello from CLI"
python teams_webhook.py "Deploy finished" --style success --title "Production Deploy"
```

Install the package locally and use the console command:

```bash
python -m pip install -e .
teams-post "Hello from installed CLI"
```

Use the optional `requests` transport:

```bash
python -m pip install requests
python teams_webhook.py "Hello from CLI" --transport requests
```

Or install the optional dependency through the package metadata:

```bash
python -m pip install -e '.[requests]'
teams-post "Hello from requests transport" --transport requests
```

Send a full Teams payload from a JSON file:

```bash
teams-post --payload-file payload.json
make post-json
```

Send an Adaptive Card document and have the CLI wrap it into a Teams message:

```bash
teams-post --payload-file card.json --payload-type adaptive-card
make post-card
```

Send JSON from stdin:

```bash
cat payload.json | teams-post --payload-file -
cat card.json | teams-post --payload-file - --payload-type adaptive-card
```

Emit JSON logs for CI systems:

```bash
teams-post "Deploy finished" --log-format json
```

Import the client in your own code:

```python
from teams_webhook import TeamsWebhookClient

client = TeamsWebhookClient("https://your-webhook-url")
client.send_text("Hello from Python")
```

Configure retries and choose transport in code:

```python
from teams_webhook import TeamsWebhookClient

client = TeamsWebhookClient(
	"https://your-webhook-url",
	timeout=10.0,
	max_retries=3,
	backoff_seconds=1.0,
	use_requests=True,
)

client.send_success("Deploy succeeded", title="Production Deploy")
```

Retry behavior:

- Retries happen for `429` and `5xx` responses.
- Delay uses exponential backoff: `backoff_seconds * 2^(attempt - 1)`.
- Transport errors are retried as transient failures.

Structured logging:

- CLI logs are written to stderr.
- `--log-format text` prints readable key/value lines.
- `--log-format json` prints one JSON object per event for CI parsing.
- `--log-format none` suppresses CLI logs.

Smoke tests:

- Run `make test` to verify the client builds payloads and loads JSON input correctly.

GitHub Actions:

- The sample workflow in `.github/workflows/post-to-teams.yml` installs the project with `make install-requests`, runs `make test`, and then posts a success or failure message.
- Set a repository secret named `TEAMS_WEBHOOK_URL` before enabling it.

Note: this folder is not currently inside a Git repository, so the workflow keeps a generic `main` plus `pull_request` trigger instead of being tailored to repository-specific branch names.