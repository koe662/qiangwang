import os

from ecdsa import SECP256k1, SigningKey


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRIVATE_KEY_PATH = os.getenv(
    "PRIVATE_KEY_PATH",
    os.path.join(BASE_DIR, "runtime", "private.pem"),
)


def ensure_key() -> None:
    if os.path.exists(PRIVATE_KEY_PATH):
        return

    os.makedirs(os.path.dirname(PRIVATE_KEY_PATH), exist_ok=True)
    signing_key = SigningKey.generate(curve=SECP256k1)
    with open(PRIVATE_KEY_PATH, "wb") as key_file:
        key_file.write(signing_key.to_pem())


if __name__ == "__main__":
    ensure_key()
