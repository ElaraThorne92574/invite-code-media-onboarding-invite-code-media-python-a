import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from invite_onboarding import CreatorSignup, InfraiClient, onboard_creator


class FakeClient(InfraiClient):
    def __init__(self) -> None:
        super().__init__("test-key", "https://example.test")
        self.calls = []

    def post(self, path, body):
        self.calls.append((path, body))
        if path == "/v1/auth/user/create":
            return {"ok": True, "data": {"user_id": "user_123"}, "error": None, "metadata": {}}
        return {"ok": True, "data": {"session_id": "session_123"}, "error": None, "metadata": {}}


def test_accepted_invite_creates_user_then_session() -> None:
    client = FakeClient()
    result = onboard_creator(
        client,
        CreatorSignup("ava@example.com", "local-password", "Ava", "MEDIA-2026"),
    )
    assert result.user_id == "user_123"
    assert [path for path, _ in client.calls] == [
        "/v1/auth/user/create", "/v1/auth/session/create"
    ]
    assert client.calls[1][1]["user_id"] == "user_123"


def test_rejected_invite_does_not_call_api() -> None:
    client = FakeClient()
    try:
        onboard_creator(
            client,
            CreatorSignup("ava@example.com", "local-password", "Ava", "WRONG"),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("an unaccepted invite must stop onboarding")
    assert client.calls == []
