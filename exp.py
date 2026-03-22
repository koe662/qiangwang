from ecdsa import SigningKey
from hashlib import sha256
import base64
import json

# 1. 这里的私钥内容来自你提供的 private.pem 文件
pem_data = b"""-----BEGIN EC PRIVATE KEY-----
MHQCAQEEIKssMVlNQJa7yB1i+7vvSrRT/g0CoM6af07NffpPM/tYoAcGBSuBBAAKoUQDQgAEjdco
0ftdl1Hv5XZ3kxzSoGcX2y44R/wk5zuL8rBaOeSh7JzqwO6C2WIQ5ttR9sJwtHgUO6fbBxk5Bl/U
X3I/yg==
-----END EC PRIVATE KEY-----
"""

# 加载私钥
sk = SigningKey.from_pem(pem_data)

# 2. 构造 Payload，满足 username == "admin" 的条件
payload_data = {"username": "admin"}
payload_json = json.dumps(payload_data).encode()
payload_b64 = base64.b64encode(payload_json).decode()

# 3. 对 Payload 进行签名
# server.py 中的验证逻辑是对 payload 的 base64 字符串部分进行 sha256 摘要，然后验证签名
msg = payload_b64.encode()
msg_digest = sha256(msg).digest()
signature = sk.sign_digest(msg_digest)
signature_b64 = base64.b64encode(signature).decode()

# 4. 拼接最终的 Token
token = f"{payload_b64}.{signature_b64}"

print("-" * 30)
print("Forged Admin Token:")
print(token)
print("-" * 30)