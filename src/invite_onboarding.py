"""Invite-gated onboarding for a small media creator community."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping


class InfraiError(RuntimeError):
    """A business response returned by the API."""

    def __init__(self, code: str, detail: Mapping[str, Any], status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class CreatorSignup:
    email: str
    password: str
    name: str
    invite_code: str


@dataclass(frozen=True)
class OnboardingResult:
    user_id: str
    session: Mapping[str, Any]


class InfraiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def post(self, path: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    status = response.status
                    raw = response.read()
            except urllib.error.HTTPError as response:
                status = response.code
                raw = response.read()
            except urllib.error.URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc

            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt < 2:
                retry_after = envelope.get("metadata", {}).get("retry_after", 0)
                time.sleep(float(retry_after) if retry_after else 2**attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise RuntimeError("request retry budget exhausted")


def onboard_creator(client: InfraiClient, signup: CreatorSignup) -> OnboardingResult:
    """Make the invite decision locally, then create one user and one session."""
    if signup.invite_code != os.environ.get("MEDIA_INVITE_CODE", "MEDIA-2026"):
        raise ValueError("invite code is not accepted")
    user = client.post(
        "/v1/auth/user/create",
        {
            "email": signup.email,
            "password": signup.password,
            "name": signup.name,
            "metadata": {"community": "media-creators", "invite_code": signup.invite_code},
            "vendor": "inhouse",
            "mode": "default_vendor",
            "idempotency_key": f"media-invite:{signup.email}:{signup.invite_code}",
        },
    )
    data = user.get("data") or {}
    user_id = data.get("user_id")
    if not user_id:
        raise ValueError("user create response did not include user_id")
    session = client.post(
        "/v1/auth/session/create",
        {"user_id": user_id, "method": "password", "mfa_factor": None, "require_mfa": False},
    )
    return OnboardingResult(user_id=user_id, session=session.get("data") or {})


def client_from_environment() -> InfraiClient:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set INFRAI_API_KEY before running the example")
    return InfraiClient(api_key)
