# Token Verify Server for GZCTF

This repository contains a deployable challenge service for GZCTF dynamic containers.

## Challenge model

- Players can query the public key from `/api/pubkey`
- Players can tune the training parameters through `/api/set_param`
- Players can collect timing and signature samples from `/api/train`
- The private key is not stored in the public repository
- The container generates its own ECDSA private key at startup

## Files

- `server.py`: Flask application
- `ensure_key.py`: generates a runtime private key if it does not exist
- `entrypoint.sh`: container startup script
- `templates/`: web pages
- `static/`: CSS
- `requirements.txt`: Python dependencies
- `Dockerfile`: image definition

## Runtime secrets

The service uses:

- `PRIVATE_KEY_PATH` default: `/var/ctf/private.pem`
- `FLAG_PATH` default: `/var/ctf/flag.txt`
- `GZCTF_FLAG`: injected by GZCTF at container startup

The repository should not contain:

- `private.pem`
- local exploit scripts
- writeups

## Local run

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:GZCTF_FLAG="flag{local_test}"
python ensure_key.py
python server.py
```

Open `http://127.0.0.1:5000/set_token`.

## Docker build

```powershell
docker build -t qiangwang:latest .
docker run --rm -p 5000:5000 -e GZCTF_FLAG="flag{local_test}" qiangwang:latest
```

## GZCTF

Recommended challenge settings:

- Image: your registry image tag
- Port: `5000`
- Dynamic flag: enabled

The private key is generated inside the container, so public source code does not expose `d`.
