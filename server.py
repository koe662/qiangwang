import base64
import json
import os
from functools import wraps
from hashlib import sha256
from random import getrandbits, shuffle
from time import time_ns

from ecdsa import BadSignatureError, SigningKey
from flask import Flask, jsonify, redirect, render_template, request, url_for


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRIVATE_KEY_PATH = os.getenv(
    "PRIVATE_KEY_PATH",
    os.path.join(BASE_DIR, "runtime", "private.pem"),
)
FLAG_PATH = os.getenv("FLAG_PATH", os.path.join(BASE_DIR, "flag.txt"))


def load_flag() -> str:
    flag_from_env = os.getenv("GZCTF_FLAG")
    if flag_from_env:
        return flag_from_env

    try:
        with open(FLAG_PATH, "r", encoding="utf-8") as flag_file:
            return flag_file.read().strip() or "flag{flag_file_is_empty}"
    except FileNotFoundError:
        return "flag{local_development_flag}"


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update(
        JSON_AS_ASCII=False,
        MAX_CONTENT_LENGTH=16 * 1024,
    )

    with open(PRIVATE_KEY_PATH, "rb") as key_file:
        pem_data = key_file.read()

    sk = SigningKey.from_pem(pem_data)
    vk = sk.verifying_key

    state = {
        "kbits": 256,
        "train_times": 1,
        "ncount": 1,
    }

    def get_nbits_k(nbits: int) -> int:
        while True:
            k = getrandbits(nbits)
            if k.bit_length() == nbits:
                return k

    def parse_token(token: str) -> dict:
        parts = token.split(".")
        if len(parts) != 2:
            raise ValueError("token format should be payload.signature")

        payload_b64, signature_b64 = parts
        message = payload_b64.encode("utf-8")
        digest = sha256(message).digest()
        signature = base64.b64decode(signature_b64, validate=True)
        vk.verify_digest(signature, digest)

        payload_raw = base64.b64decode(payload_b64, validate=True)
        payload = json.loads(payload_raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("payload must be a json object")
        return payload

    def verify_token(token: str) -> tuple[bool, dict | None, str]:
        try:
            payload = parse_token(token)
        except (ValueError, json.JSONDecodeError, BadSignatureError, TypeError):
            return False, None, "Invalid token"
        except Exception:
            return False, None, "Token verification failed"

        username = payload.get("username")
        if not isinstance(username, str) or not username:
            return False, None, "Token payload missing username"

        return True, payload, "Token is valid"

    def token_required(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            token = request.cookies.get("token")
            if not token:
                return redirect(url_for("failure", reason="missing"))

            valid, payload, _ = verify_token(token)
            if not valid or payload is None:
                return redirect(url_for("failure", reason="invalid"))

            request.user = payload["username"]
            request.user_payload = payload
            return view_func(*args, **kwargs)

        return wrapped

    @app.route("/")
    def index():
        return redirect(url_for("set_token"))

    @app.route("/set_token", methods=["GET", "POST"])
    def set_token():
        token = request.cookies.get("token", "")
        validation = None

        if request.method == "POST":
            token = request.form.get("token", "").strip()
            response = redirect(url_for("welcome"))
            response.set_cookie(
                "token",
                token,
                httponly=True,
                max_age=24 * 60 * 60,
                samesite="Lax",
            )
            return response

        if token:
            valid, payload, message = verify_token(token)
            validation = {
                "valid": valid,
                "message": message,
                "username": payload.get("username") if payload else None,
            }

        return render_template("set_token.html", token=token, validation=validation)

    @app.route("/welcome")
    @token_required
    def welcome():
        if request.user == "admin":
            return render_template(
                "welcome.html",
                username=request.user,
                flag=load_flag(),
            )
        return redirect(url_for("guest"))

    @app.route("/guest")
    @token_required
    def guest():
        return render_template("guest.html", username=request.user)

    @app.route("/failure")
    def failure():
        reason = request.args.get("reason", "invalid")
        reason_map = {
            "missing": "No token was found. Submit a token first.",
            "invalid": "Token validation failed. Signature or payload is invalid.",
        }
        return render_template(
            "failure.html",
            error_message=reason_map.get(reason, "Token validation failed."),
        )

    @app.route("/logout", methods=["POST"])
    def logout():
        response = redirect(url_for("set_token"))
        response.delete_cookie("token")
        return response

    @app.route("/api/pubkey", methods=["GET"])
    def pubkey():
        return jsonify({"vk": vk.to_string().hex()}), 200

    @app.route("/api/verify", methods=["POST"])
    def api_verify():
        data = request.get_json(silent=True) or {}
        token = str(data.get("token", "")).strip()
        if not token:
            return jsonify({"valid": False, "reason": "token is required"}), 400

        valid, payload, message = verify_token(token)
        return (
            jsonify(
                {
                    "valid": valid,
                    "reason": message,
                    "payload": payload if valid else None,
                }
            ),
            200,
        )

    @app.route("/api/set_param", methods=["POST"])
    def set_param():
        data = request.get_json(silent=True) or {}

        kbits = int(data.get("kbits", state["kbits"]))
        train_times = int(data.get("train", state["train_times"]))
        ncount = int(data.get("ncount", state["ncount"]))

        reason = ""
        if kbits < 240:
            kbits = 256
            reason = "kbits is too small"

        state["kbits"] = kbits
        state["train_times"] = max(train_times, 1)
        state["ncount"] = max(ncount, 1)

        return (
            jsonify(
                {
                    "status": 0,
                    "reason": reason,
                    "params": {
                        "kbits": state["kbits"],
                        "train_times": state["train_times"],
                        "ncount": state["ncount"],
                    },
                }
            ),
            200,
        )

    @app.route("/api/train", methods=["GET"])
    def train():
        message = b"Not your keys, not your coins!"
        message_digest = sha256(message).digest()

        nonces = []
        for _ in range(state["ncount"]):
            nonces.append(get_nbits_k(256))
            nonces.append(get_nbits_k(state["kbits"]))

        shuffle(nonces)

        costs = []
        sigs = []
        for nonce in nonces:
            elapsed_ns = 0
            for _ in range(state["train_times"]):
                start = time_ns()
                signature = sk.sign_digest(message_digest, k=nonce)
                elapsed_ns += time_ns() - start
            sigs.append(signature.hex())
            costs.append(elapsed_ns)

        return jsonify({"costs": costs, "sigs": sigs}), 200

    return app


app = create_app()


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
