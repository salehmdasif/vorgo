import sqlite3
import base64
import sys

# Try importing cryptography
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("CRYPTOGRAPHY_MODULE_NOT_FOUND")
    sys.exit(0)

def pad(key, length=32):
    key_len = len(key)
    if key_len < length:
        key = key + '}' * (length - key_len)
    elif key_len > length:
        key = key[:length]
    return key.encode('utf-8')

def decrypt(ciphertext, key, pad_length=32):
    ciphertext = base64.b64decode(ciphertext)
    iv_size = 16
    iv = ciphertext[:iv_size]
    cipher = Cipher(algorithms.AES(pad(key, pad_length)), modes.CFB8(iv), default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext[iv_size:]) + decryptor.finalize()

db_path = r"C:\Users\saleh\AppData\Roaming\pgAdmin\pgadmin4.db"
master_pwd = "gbqVdrfzNqKFr3ot"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name, username, password FROM server WHERE name = 'PostgreSQL 18';")
row = cursor.fetchone()

if row:
    name, username, enc_password = row
    print(f"Server: {name}")
    print(f"Username: {username}")
    print(f"Encrypted Password (Hex): {enc_password}")
    if enc_password:
        try:
            # First decode hex to ascii base64 string
            base64_str = bytes.fromhex(enc_password).decode('ascii')
            print(f"Base64 String: {base64_str}")
            for length in [16, 24, 32]:
                try:
                    dec_pwd = decrypt(base64_str, master_pwd, length)
                    print(f"\n--- Pad Length: {length} ---")
                    print(f"Decrypted Password (raw): {dec_pwd}")
                    try:
                        print(f"Decrypted Password (UTF-8): {dec_pwd.decode('utf-8')}")
                    except Exception as e:
                        print(f"Failed to decode UTF-8: {e}")
                except Exception as e:
                    print(f"Decryption failed for pad length {length}: {e}")
        except Exception as e:
            print(f"Hex decoding or processing failed: {e}")
    else:
        print("No password saved for this server.")
else:
    print("Server 'PostgreSQL 18' not found in pgAdmin database.")

conn.close()
