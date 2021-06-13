try:
    from gmssl.sm3 import sm3_hash


    def sm3u(uid: str) -> str:
        # ie(uid) == 10^9 == 9
        # ie(rtn) == 16^8 ?= 10
        b0 = [194, 183, 196, 169, 181, 196, 192, 199]
        b2 = bytearray(uid + 'Py6ensh1n', encoding='ANSI')
        for _ in range(91):
            b2 = bytearray.fromhex(sm3_hash(b2))
        for i in range(len(b2)):
            b0[i % 8] ^= b2[i]
        return bytes(b0).hex()


    def sm3r(rid: str) -> str:
        # ie(rid) == 10^19 == 19
        # ie(rtn) == 16^32 ?= 39
        b = bytes.fromhex(sm3_hash(bytearray(rid, encoding='ANSI')))
        return bytes([b[i] ^ b[i + 1] for i in range(0, len(b), 2)]).hex()


except ImportError:
    from hashlib import sha256

    def sm3u(uid: str) -> str:
        # ie(uid) == 10^9 == 9
        # ie(rtn) == 16^8 ?= 10
        b0 = [149, 138, 169, 196, 118, 169, 129, 199]
        b2 = bytearray(uid + 'Py6ensh1n', encoding='ANSI')
        for _ in range(91):
            b2 = sha256(b2).digest()
        for i in range(len(b2)):
            b0[i % 8] ^= b2[i]
        return bytes(b0).hex()


    def sm3r(rid: str) -> str:
        # ie(rid) == 10^19 == 19
        # ie(rtn) == 16^32 ?= 39
        b = sha256(bytes(rid, encoding='ANSI')).digest()
        return bytes([b[i] ^ b[i + 1] for i in range(0, len(b), 2)]).hex()

    sm3_hash = None  # 这一行并没有用，只是为了不被IDE警告而已。


if __name__ == '__main__':
    print(sm3u('l065004Z9'))
