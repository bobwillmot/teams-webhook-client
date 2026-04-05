import os

from teams_webhook import TeamsWebhookClient


def main() -> None:
    webhook_url = os.environ["TEAMS_WEBHOOK_URL"]
    client = TeamsWebhookClient(
        webhook_url,
        max_retries=3,
        backoff_seconds=1.0,
        use_requests=False,
    )

    client.send_text("Nightly job completed")
    client.send_success("Deployment finished for payments-api", title="Production Deploy")
    client.send_warning("Queue depth is elevated")
    client.send_error("ETL job failed after 3 retries")
    client.send_fact_card(
        title="Build Summary",
        message="Build completed with the following details:",
        facts={
            "Service": "payments-api",
            "Environment": "prod",
            "Version": "2026.04.04.1",
            "Status": "Healthy",
        },
    )


if __name__ == "__main__":
    main()