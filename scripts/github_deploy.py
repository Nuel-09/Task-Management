import argparse
import json
import sys
import urllib.error
import urllib.request


API_BASE = "https://api.github.com"


def _request(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url=url, data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if payload is not None:
        req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8")
        raise RuntimeError(f"GitHub API error {exc.code}: {error_body}") from exc


def create_deployment(
    repo: str,
    token: str,
    ref: str,
    environment: str,
    environment_url: str,
    description: str,
) -> int:
    url = f"{API_BASE}/repos/{repo}/deployments"
    payload = {
        "ref": ref,
        "environment": environment,
        "required_contexts": [],
        "auto_merge": False,
        "description": description,
        "transient_environment": environment != "prod",
        "production_environment": environment == "prod",
        "payload": {"environment_url": environment_url},
    }
    response = _request("POST", url, token, payload)
    return int(response["id"])


def update_deployment_status(
    repo: str,
    token: str,
    deployment_id: int,
    state: str,
    environment: str,
    environment_url: str,
    log_url: str | None = None,
) -> None:
    url = f"{API_BASE}/repos/{repo}/deployments/{deployment_id}/statuses"
    payload = {
        "state": state,
        "environment": environment,
        "environment_url": environment_url,
    }
    if log_url:
        payload["log_url"] = log_url

    _request("POST", url, token, payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create/update GitHub deployments.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("--repo", required=True)
    create_parser.add_argument("--token", required=True)
    create_parser.add_argument("--ref", required=True)
    create_parser.add_argument("--environment", required=True)
    create_parser.add_argument("--environment-url", required=True)
    create_parser.add_argument("--description", default="Jenkins deployment")
    create_parser.add_argument("--output-file")

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--repo", required=True)
    update_parser.add_argument("--token", required=True)
    update_parser.add_argument("--deployment-id", required=True, type=int)
    update_parser.add_argument("--state", required=True)
    update_parser.add_argument("--environment", required=True)
    update_parser.add_argument("--environment-url", required=True)
    update_parser.add_argument("--log-url")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "create":
            deployment_id = create_deployment(
                repo=args.repo,
                token=args.token,
                ref=args.ref,
                environment=args.environment,
                environment_url=args.environment_url,
                description=args.description,
            )
            if args.output_file:
                with open(args.output_file, "w", encoding="utf-8") as file:
                    file.write(str(deployment_id))
            print(deployment_id)
        else:
            update_deployment_status(
                repo=args.repo,
                token=args.token,
                deployment_id=args.deployment_id,
                state=args.state,
                environment=args.environment,
                environment_url=args.environment_url,
                log_url=args.log_url,
            )
            print("ok")
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
