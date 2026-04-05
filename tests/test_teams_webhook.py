import io
import json
import sys
import tempfile
import unittest
from unittest import mock

from teams_webhook import TeamsWebhookClient, TeamsWebhookError, _load_json_payload, _make_cli_logger


class RecordingClient(TeamsWebhookClient):
    def __init__(self) -> None:
        super().__init__("https://example.test/webhook")
        self.last_payload = None

    def _post_json(self, payload: dict) -> str:
        self.last_payload = payload
        return "ok"


class RetryingClient(TeamsWebhookClient):
    def __init__(self, responses, **kwargs) -> None:
        super().__init__("https://example.test/webhook", **kwargs)
        self._responses = list(responses)

    def _post_json_urllib(self, payload: dict) -> str:
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class TeamsWebhookTests(unittest.TestCase):
    def test_send_text_builds_adaptive_card_payload(self) -> None:
        client = RecordingClient()

        response = client.send_text("Hello from test", title="Greeting")

        self.assertEqual(response, "ok")
        self.assertIsNotNone(client.last_payload)
        self.assertEqual(client.last_payload["type"], "message")
        attachment = client.last_payload["attachments"][0]
        self.assertEqual(attachment["contentType"], "application/vnd.microsoft.card.adaptive")
        body = attachment["content"]["body"]
        self.assertEqual(body[0]["text"], "Greeting")
        self.assertEqual(body[1]["text"], "Hello from test")

    def test_send_payload_passes_through_unchanged(self) -> None:
        client = RecordingClient()
        payload = {"type": "message", "attachments": []}

        client.send_payload(payload)

        self.assertEqual(client.last_payload, payload)

    def test_load_json_payload_reads_file(self) -> None:
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8") as handle:
            json.dump({"type": "message"}, handle)
            handle.flush()

            payload = _load_json_payload(handle.name)

        self.assertEqual(payload, {"type": "message"})

    def test_load_json_payload_reads_stdin(self) -> None:
        with mock.patch.object(sys, "stdin", io.StringIO('{"type": "message"}')):
            payload = _load_json_payload("-")

        self.assertEqual(payload, {"type": "message"})

    def test_load_json_payload_rejects_non_object_json(self) -> None:
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8") as handle:
            json.dump([1, 2, 3], handle)
            handle.flush()

            with self.assertRaisesRegex(RuntimeError, "top level"):
                _load_json_payload(handle.name)

    def test_retryable_failure_retries_and_logs_events(self) -> None:
        events = []
        client = RetryingClient(
            [
                TeamsWebhookError("retry me", status_code=429, retryable=True),
                "ok",
            ],
            max_retries=2,
            backoff_seconds=0.5,
            log_handler=lambda event, fields: events.append((event, fields)),
        )

        with mock.patch("teams_webhook.time.sleep") as sleep_mock:
            result = client.send_payload({"type": "message"})

        self.assertEqual(result, "ok")
        sleep_mock.assert_called_once_with(0.5)
        self.assertEqual([event for event, _ in events], [
            "send_attempt",
            "send_failure",
            "retry_scheduled",
            "send_attempt",
            "send_success",
        ])

    def test_non_retryable_failure_does_not_retry(self) -> None:
        client = RetryingClient(
            [TeamsWebhookError("bad request", status_code=400, retryable=False)],
            max_retries=2,
            backoff_seconds=0.5,
        )

        with mock.patch("teams_webhook.time.sleep") as sleep_mock:
            with self.assertRaisesRegex(RuntimeError, "bad request"):
                client.send_payload({"type": "message"})

        sleep_mock.assert_not_called()

    def test_make_cli_logger_json_emits_json_record(self) -> None:
        logger = _make_cli_logger("json")
        stderr = io.StringIO()

        with mock.patch.object(sys, "stderr", stderr):
            logger("send_success", {"attempt": 1, "transport": "urllib"})

        record = json.loads(stderr.getvalue())
        self.assertEqual(record["event"], "send_success")
        self.assertEqual(record["attempt"], 1)
        self.assertEqual(record["transport"], "urllib")

    def test_make_cli_logger_none_returns_none(self) -> None:
        self.assertIsNone(_make_cli_logger("none"))


if __name__ == "__main__":
    unittest.main()