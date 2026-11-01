import base64, gzip, sys, pathlib
p = pathlib.Path(r"cs.b64")
data = p.read_bytes()
print("len", len(data), "head", data[:16])
try:
    dec = base64.b64decode(data, validate=False)
    print("b64len", len(dec), "head", dec[:16])
    if dec[:2] == b"\x1f\x8b":
        dec = gzip.decompress(dec)
    out = p.with_suffix(".cpp")
    out.write_bytes(dec)
    print("wrote", out, len(dec))
except Exception as e:
    print("err", e)
