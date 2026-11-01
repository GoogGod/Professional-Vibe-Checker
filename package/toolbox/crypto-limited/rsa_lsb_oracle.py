# RSA LSB/parity oracle (эталон)
import requests, json, sys
BASE = 'http://TARGET:PORT'
def get_int(url):
    return json.loads(requests.get(BASE+url, timeout=10).text)
pub = get_int('/public_key')
n, e, c = int(pub['n']), int(pub['e']), int(pub['ciphertext'])
def even(ct): return get_int(f'/oracle?ciphertext={ct}')['even']
lo, hi = 0, n
for i in range(n.bit_length()):
    c = c * pow(2, e, n) % n
    mid = (lo + hi)//2
    if even(c): hi = mid
    else: lo = mid
m = hi
print(m.to_bytes((m.bit_length()+7)//8, 'big'))
