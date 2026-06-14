import ctypes
from ctypes import wintypes


class CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.c_void_p),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


advapi32 = ctypes.windll.advapi32
CredReadW = advapi32.CredReadW
CredReadW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.POINTER(ctypes.POINTER(CREDENTIAL)),
]
CredReadW.restype = wintypes.BOOL

CredFree = advapi32.CredFree
CredFree.argtypes = [ctypes.c_void_p]
CredFree.restype = None


def get_credential(target_name, cred_type=1):
    p_cred = ctypes.POINTER(CREDENTIAL)()
    res = CredReadW(target_name, cred_type, 0, ctypes.byref(p_cred))
    if res:
        try:
            cred = p_cred.contents
            blob_size = cred.CredentialBlobSize
            blob_ptr = cred.CredentialBlob
            if blob_ptr:
                # Read bytes
                blob_bytes = ctypes.string_at(blob_ptr, blob_size)
                # It might be UTF-16LE or UTF-8 or raw ASCII
                try:
                    password = blob_bytes.decode("utf-16-le")
                except Exception:
                    try:
                        password = blob_bytes.decode("utf-8")
                    except Exception:
                        password = blob_bytes.decode("latin-1")
                return password
        finally:
            CredFree(p_cred)
    return None


targets = ["pgAdmin4", "LegacyGeneric:target=pgAdmin4"]
for t in targets:
    pwd = get_credential(t)
    if pwd:
        print(f"Target: {t}")
        print(f"Master Password: {pwd}")
    else:
        # Try type 2 (CRED_TYPE_DOMAIN_PASSWORD) or others
        for ctypes_val in range(1, 4):
            pwd = get_credential(t, ctypes_val)
            if pwd:
                print(f"Target: {t} (Type: {ctypes_val})")
                print(f"Master Password: {pwd}")
                break
