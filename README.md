# Token Verify Server for GZCTF

This repository contains a ready-to-build Flask challenge for GZCTF dynamic containers.

## Features

- Verifies ECDSA-signed tokens from the web UI
- Keeps the original challenge APIs: `/api/pubkey`, `/api/set_param`, `/api/train`
- Adds `/api/verify` for direct token validation
- Reads the dynamic flag from `GZCTF_FLAG` and shows it only on the admin page
- Can be built directly by GitHub Actions or any container registry pipeline

## Files

- `server.py`: Flask application entry
- `entrypoint.sh`: container startup script for `GZCTF_FLAG`
- `private.pem`: signing key used by the challenge
- `templates/`: HTML templates
- `static/`: CSS assets
- `requirements.txt`: Python dependencies
- `Dockerfile`: final container image definition

## Local run

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:GZCTF_FLAG="flag{local_test}"
python server.py
```

Open `http://127.0.0.1:5000/set_token`.

## Docker build

```powershell
docker build -t yourname/token-verify:latest .
docker run --rm -p 5000:5000 -e GZCTF_FLAG="flag{local_test}" yourname/token-verify:latest
```

## GZCTF usage

1. Push this image to Docker Hub, GHCR, or another registry.
2. Create a `Dynamic Container` challenge in GZCTF.
3. Set the image name to your pushed image tag.
4. Set the container port to `5000`.
5. Let GZCTF inject `GZCTF_FLAG` dynamically.

The container does not rely on `EXPOSE`, which matches GZCTF deployment expectations.
