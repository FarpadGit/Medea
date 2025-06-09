import json
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from main.settings import env

key = env("AES_KEY").encode()

def encrypt(data):
    cipher = AES.new(key, AES.MODE_CBC)
    cyphertext_bytes = cipher.encrypt(pad(data, AES.block_size))
    iv = b64encode(cipher.iv).decode("utf-8")
    ct = b64encode(cyphertext_bytes).decode("utf-8")
    result = json.dumps({"iv": iv, "ciphertext": ct})
    encoded_result = b64encode(result.encode("utf-8"))

    return encoded_result

def decrypt(data):
    try:
        decoded_data = b64decode(data)
        secret_pair = json.loads(decoded_data)
        iv = b64decode(secret_pair["iv"])
        ct = b64decode(secret_pair["ciphertext"])
        cipher = AES.new(key, AES.MODE_CBC, iv)
        message = unpad(cipher.decrypt(ct), AES.block_size)
        return message.decode("utf-8")
    except (ValueError, KeyError):
        print("Incorrect decryption")