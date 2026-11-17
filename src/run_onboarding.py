import json
import os

from invite_onboarding import CreatorSignup, client_from_environment, onboard_creator


def main() -> None:
    email = os.environ.get("ONBOARDING_EMAIL")
    if not email:
        raise RuntimeError("Set ONBOARDING_EMAIL before running the example")
    signup = CreatorSignup(
        email=email,
        password="choose-a-local-password",
        name="Ava Creator",
        invite_code="MEDIA-2026",
    )
    result = onboard_creator(client_from_environment(), signup)
    print(json.dumps({"user_id": result.user_id, "session": result.session}, indent=2))


if __name__ == "__main__":
    main()
