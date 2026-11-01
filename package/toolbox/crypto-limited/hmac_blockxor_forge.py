# HMAC block_xor forge (эталон)
import requests, json
BASE='http://TARGET:PORT'
def post(path, payload):
    r=requests.post(BASE+path, json=payload, timeout=10); return r.text
t=json.loads(post('/oracle', {'msg':'give_me_flag_plz'}))
bx=bytes.fromhex(t['block_xor'])
mac_in=b''.join(bx[i:i+1]+b'\x00'*7 for i in range(4))
print(post('/verify', {'msg':'give_me_flag_plz','mac':mac_in.hex()}))
