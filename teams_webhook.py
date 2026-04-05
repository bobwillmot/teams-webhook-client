import argparse
from datetime import datetime, timezone
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Callable


class TeamsWebhookError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, retryable: bool = False) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class TeamsWebhookClient:
    def __init__(
        self,
        webhook_url: str,
        timeout: float = 10.0,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
        use_requests: bool = False,
        log_handler: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        if not webhook_url:
            raise ValueError("webhook_url is required")
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if backoff_seconds < 0:
            raise ValueError("backoff_seconds must be >= 0")
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.use_requests = use_requests
        self.log_handler = log_handler

    def send_text(self, text: str, title: str | None = None) -> str:
        body = []
        if title:
            body.append(
                {
                    "type": "TextBlock",
                    "text": title,
                    "weight": "Bolder",
                    "size": "Medium",
                    "wrap": True,
                }
            )
        body.append(
            {
                "type": "TextBlock",
                "text": text,
                "wrap": True,
            }
        )
        return self._post_card(body)

    def send_success(self, text: str, title: str = "Success") -> str:
        return self._post_card(
            [
                {
                    "type": "TextBlock",
                    "text": title,
                    "weight": "Bolder",
                    "size": "Medium",
                    "color": "Good",
                    "wrap": True,
                },
                {
                    "type": "TextBlock",
                    "text": text,
                    "wrap": True,
                },
            ]
        )

    def send_warning(self, text: str, title: str = "Warning") -> str:
        return self._post_card(
            [
                {
                    "type": "TextBlock",
                    "text": title,
                    "weight": "Bolder",
                    "size": "Medium",
                    "color": "Warning",
                    "wrap": True,
                },
                {
                    "type": "TextBlock",
                    "text": text,
                    "wrap": True,
                },
            ]
        )

    def send_error(self, text: str, title: str = "Error") -> str:
        return self._post_card(
            [
                {
                    "type": "TextBlock",
                    "text": title,
                    "weight": "Bolder",
                    "size": "Medium",
                    "color": "Attention",
                    "wrap": True,
                },
                {
                    "type": "TextBlock",
                    "text": text,
                    "wrap": True,
                },
            ]
        )

    def send_fact_card(
        self,
        title: str,
        facts: dict[str, str],
        message: str | None = None,
    ) -> str:
        body = [
            {
                "type": "TextBlock",
                "text": title,
                "weight": "Bolder",
                "size": "Medium",
                "wrap": True,
            }
        ]

        if message:
            body.append(
                {
                    "type": "TextBlock",
                    "text": message,
                    "wrap": True,
                }
            )

        body.append(
            {
                "type": "FactSet",
                "facts": [{"title": key, "value": value} for key, value in facts.items()],
            }
        )

        return self._post_card(body)

    def send_adaptive_card(self, card: dict[str, Any]) -> str:
        return self.send_payload(_wrap_adaptive_card(card))

    def send_payload(self, payload: dict[str, Any]) -> str:
        return self._post_json(payload)

    def _post_card(self, body: list[dict]) -> str:
        return self.send_adaptive_card(
            {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": body,
            }
        )

    def _post_json(self, payload: dict) -> str:
        attempts = self.max_retries + 1
        last_error: TeamsWebhookError | None = None

        for attempt in range(1, attempts + 1):
            self._log(
                "send_attempt",
                attempt=attempt,
                max_attempts=attempts,
                transport=self._transport_name,
            )
            try:
                if self.use_requests:
                    response_body = self._post_json_requests(payload)
                else:
                    response_body = self._post_json_urllib(payload)
                self._log(
                    "send_success",
                    attempt=attempt,
                    max_attempts=attempts,
                    transport=self._transport_name,
                )
                return response_body
            except TeamsWebhookError as exc:
                last_error = exc
                self._log(
                    "send_failure",
                    attempt=attempt,
                    max_attempts=attempts,
                    transport=self._transport_name,
                    status_code=exc.status_code,
                    retryable=exc.retryable,
                    error=str(exc),
                )
                if attempt >= attempts or not exc.retryable:
                    raise
                delay_seconds = self.backoff_seconds * (2 ** (attempt - 1))
                self._log(
                    "retry_scheduled",
                    attempt=attempt,
                    next_attempt=attempt + 1,
                    max_attempts=attempts,
                    delay_seconds=delay_seconds,
                )
                time.sleep(delay_seconds)

        if last_error is not None:
            raise last_error
        raise TeamsWebhookError("Teams webhook failed with an unknown error")

    def _post_json_urllib(self, payload: dict) -> str:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8", errors="replace")
                if response.status >= 400:
                    raise TeamsWebhookError(
                        f"Teams webhook failed: {response.status} {response_body}",
                        status_code=response.status,
                        retryable=self._should_retry_status(response.status),
                    )
                return response_body
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise TeamsWebhookError(
                f"Teams webhook failed: {exc.code} {error_body}",
                status_code=exc.code,
                retryable=self._should_retry_status(exc.code),
            ) from exc
        except urllib.error.URLError as exc:
            raise TeamsWebhookError(
                f"Teams webhook connection failed: {exc}",
                retryable=True,
            ) from exc

    def _post_json_requests(self, payload: dict) -> str:
        try:
            import requests
        except ImportError as exc:
            raise TeamsWebhookError(
                "requests transport requested but the requests package is not installed",
                retryable=False,
            ) from exc

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise TeamsWebhookError(
                f"Teams webhook connection failed: {exc}",
                retryable=True,
            ) from exc

        response_body = response.text
        if response.status_code >= 400:
            raise TeamsWebhookError(
                f"Teams webhook failed: {response.status_code} {response_body}",
                status_code=response.status_code,
                retryable=self._should_retry_status(response.status_code),
            )
        return response_body

    @staticmethod
    def _should_retry_status(status_code: int) -> bool:
        return status_code == 429 or 500 <= status_code <= 599

    @property
    def _transport_name(self) -> str:
        return "requests" if self.use_requests else "urllib"

    def _log(self, event: str, **fields: Any) -> None:
        if self.log_handler is None:
            return
        self.log_handler(event, fields)


def _wrap_adaptive_card(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card,
            }
        ],
    }


def _load_json_payload(path: str) -> dict[str, Any]:
    if path == "-":
        raw = sys.stdin.read()
    else:
        with open(path, encoding="utf-8") as handle:
            raw = handle.read()

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TeamsWebhookError(f"Invalid JSON input: {exc}") from exc

    if not isinstance(payload, dict):
        raise TeamsWebhookError("JSON input must be an object at the top level")

    return payload


def _make_cli_logger(log_format: str) -> Callable[[str, dict[str, Any]], None] | None:
    if log_format == "none":
        return None

    def log(event: str, fields: dict[str, Any]) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **fields,
        }
        if log_format == "json":
            print(json.dumps(record, sort_keys=True), file=sys.stderr)
            return

        details = " ".join(f"{key}={value}" for key, value in record.items() if value is not None)
        print(details, file=sys.stderr)

    return log


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Post a message to a Microsoft Teams webhook")
    parser.add_argument("message", nargs="?", help="Message text to send")
    parser.add_argument("--title", help="Optional card title")
    parser.add_argument(
        "--payload-file",
        help="Path to a JSON payload file. Use '-' to read JSON from stdin.",
    )
    parser.add_argument(
        "--payload-type",
        choices=["teams", "adaptive-card"],
        default="teams",
        help="Interpret payload JSON as a full Teams payload or as Adaptive Card content.",
    )
    parser.add_argument(
        "--webhook-url",
        default=os.environ.get("TEAMS_WEBHOOK_URL"),
        help="Webhook URL. Defaults to TEAMS_WEBHOOK_URL.",
    )
    parser.add_argument(
        "--style",
        choices=["text", "success", "warning", "error"],
        default="text",
        help="Card style to send.",
    )
    parser.add_argument(
        "--transport",
        choices=["urllib", "requests"],
        default="urllib",
        help="HTTP transport implementation.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Request timeout in seconds.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Number of retries after the first attempt for retryable failures.",
    )
    parser.add_argument(
        "--backoff-seconds",
        type=float,
        default=1.0,
        help="Base exponential backoff in seconds.",
    )
    parser.add_argument(
        "--log-format",
        choices=["text", "json", "none"],
        default="text",
        help="CLI log output format. Logs are written to stderr.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if not args.webhook_url:
        parser.error("A webhook URL is required via --webhook-url or TEAMS_WEBHOOK_URL")

    if not args.payload_file and not args.message:
        parser.error("Provide either a message argument or --payload-file")

    logger = _make_cli_logger(args.log_format)

    client = TeamsWebhookClient(
        args.webhook_url,
        timeout=args.timeout,
        max_retries=args.max_retries,
        backoff_seconds=args.backoff_seconds,
        use_requests=args.transport == "requests",
        log_handler=logger,
    )

    try:
        if args.payload_file:
            payload = _load_json_payload(args.payload_file)
            if args.payload_type == "adaptive-card":
                client.send_adaptive_card(payload)
            else:
                client.send_payload(payload)
        elif args.style == "success":
            client.send_success(args.message, title=args.title or "Success")
        elif args.style == "warning":
            client.send_warning(args.message, title=args.title or "Warning")
        elif args.style == "error":
            client.send_error(args.message, title=args.title or "Error")
        else:
            client.send_text(args.message, title=args.title)
    except TeamsWebhookError as exc:
        print(str(exc))
        return 1

    print("Posted to Teams")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())