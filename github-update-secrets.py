import sys
import requests

from base64 import b64encode
from nacl import encoding, public

session = requests.session()


def encrypt(public_key: str, secret_value: str) -> str:
    """
    Encrypt a Unicode string using the public key.
    source: https://docs.github.com/en/rest/reference/actions#example-encrypting-a-secret-using-python
    """
    return b64encode(
        public.SealedBox(
            public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
        ).encrypt(secret_value.encode("utf-8"))
    ).decode("utf-8")


def main():
    _, repo, token, secret_name, secret_value = sys.argv
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }

    pub_key = session.get(
        f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
        headers=headers,
    ).json()

    encrypted_value = encrypt(pub_key["key"], secret_value)

    response = session.put(
        f"https://api.github.com/repos/{repo}/actions/secrets/{secret_name}",
        headers=headers,
        json={"encrypted_value": encrypted_value, "key_id": pub_key["key_id"]},
    )

    if response.status_code not in (201, 204):
        raise Exception("creating/updating secret failed! response is: {response.text}")


if __name__ == "__main__":
    main()
