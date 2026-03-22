import base64
import json
import os
from functools import wraps
from hashlib import sha256
from random import getrandbits, shuffle
from time import time_ns

from ecdsa import SigningKey
from flask import Flask, jsonify, redirect, render_template, request, url_for


app = Flask(__name__)

PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH", "private.pem")

with open(PRIVATE_KEY_PATH, "rb") as f:
    pem_data = f.read()

sk = SigningKey.from_pem(pem_data)
vk = sk.verifying_key

kbits = 256
train_times = 1
ncount = 1


def get_nbits_k(nbits):
    while True:
        k = getrandbits(nbits)
        if k.bit_length() == nbits:
            return k


def verify_token(token):
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return False

        msg = parts[0].encode()
        msg_digest = sha256(msg).digest()

        signature = base64.b64decode(parts[1])
        if vk.verify_digest(signature, msg_digest):
            return True
        else:
            return False
    except:
        return False


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "token" in request.cookies:
            try:
                token = request.cookies.get("token")
            except:
                return redirect(url_for("failure"))

        if not token:
            return redirect(url_for("failure"))

        valid = verify_token(token)

        if valid:
            parts = token.split(".")
            payload = parts[0]
            payload = base64.b64decode(payload)

            payload_json = json.loads(payload)
            request.user = payload_json["username"]
            return f(*args, **kwargs)
        else:
            return redirect(url_for("failure"))

    return decorated


@app.route("/set_token", methods=["GET", "POST"])
def set_token():
    if request.method == "POST":
        token = request.form.get("token")
        response = redirect(url_for("welcome"))
        response.set_cookie("token", token, httponly=True, max_age=24 * 60 * 60)
        return response
    else:
        return render_template("set_token.html")


@app.route("/")
def index():
    return redirect(url_for("set_token"))


@app.route("/welcome")
@token_required
def welcome():
    if request.user == "admin":
        return render_template("welcome.html")
    else:
        return redirect(url_for("guest"))


@app.route("/failure")
def failure():
    return render_template("failure.html")


@app.route("/guest")
def guest():
    return render_template("guest.html")


@app.route("/api/pubkey", methods=["GET"])
def pubkey():
    return jsonify({"vk": vk.to_string().hex()}), 200


@app.route("/api/set_param", methods=["POST"])
def set_param():
    global kbits, train_times, ncount
    print(sk.privkey.secret_multiplier)
    print(kbits, train_times, ncount)
    data = request.get_json()
    kbits = data.get("kbits")
    reason = ""
    if kbits < 240:
        kbits = 256
        reason = "kbits is too small"
    train_times = data.get("train")
    ncount = data.get("ncount")
    return jsonify({"status": 0, "reason": reason}), 200


@app.route("/api/train", methods=["GET"])
def train():
    message = b"Not your keys, not your coins!"
    message_digest = sha256(message).digest()

    nonces = []
    for _ in range(ncount):
        k = get_nbits_k(256)
        nonces.append(k)
        k = get_nbits_k(kbits)
        nonces.append(k)

    shuffle(nonces)

    costs = []
    sigs = []
    for k in nonces:
        tmp = 0
        for _ in range(train_times):
            start = time_ns()
            signature = sk.sign_digest(message_digest, k=k)
            end = time_ns()
            tmp += end - start

        sigs.append(signature.hex())
        costs.append(tmp)

    return jsonify({"costs": costs, "sigs": sigs}), 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
