# -*- coding: utf-8 -*-
"""AES-256-CTR 与 HMAC。只依赖标准库，青龙里不用再装加密包。"""

import hashlib
import hmac
import os

SBOX = bytes.fromhex(
    "637c777bf26b6fc53001672bfed7ab76"
    "ca82c97dfa5947f0add4a2af9ca472c0"
    "b7fd9326363ff7cc34a5e5f171d83115"
    "04c723c31896059a071280e2eb27b275"
    "09832c1a1b6e5aa0523bd6b329e32f84"
    "53d100ed20fcb15b6acbbe394a4c58cf"
    "d0efaafb434d338545f9027f503c9fa8"
    "51a3408f929d38f5bcb6da2110fff3d2"
    "cd0c13ec5f974417c4a77e3d645d1973"
    "60814fdc222a908846eeb814de5e0bdb"
    "e0323a0a4906245cc2d3ac629195e479"
    "e7c8376d8dd54ea96c56f4ea657aae08"
    "ba78252e1ca6b4c6e8dd741f4bbd8b8a"
    "703eb5664803f60e613557b986c11d9e"
    "e1f8981169d98e949b1e87e9ce5528df"
    "8ca1890dbfe6426841992d0fb054bb16"
)
RCON = (0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36)


def _xtime(value):
    return ((value << 1) ^ 0x1B) & 0xFF if value & 0x80 else (value << 1) & 0xFF


def _mul(a, b):
    result = 0
    for _ in range(8):
        if b & 1:
            result ^= a
        a = _xtime(a)
        b >>= 1
    return result


def _sub_word(word):
    return bytes(SBOX[b] for b in word)


def _rot_word(word):
    return word[1:] + word[:1]


def _xor(left, right):
    return bytes(a ^ b for a, b in zip(left, right))


def _expand(key):
    if len(key) != 32:
        raise ValueError("需要 32 字节密钥")
    words = [key[i : i + 4] for i in range(0, 32, 4)]
    index = 8
    while len(words) < 60:
        temp = words[-1]
        if index % 8 == 0:
            temp = _xor(_sub_word(_rot_word(temp)), bytes((RCON[index // 8], 0, 0, 0)))
        elif index % 8 == 4:
            temp = _sub_word(temp)
        words.append(_xor(words[-8], temp))
        index += 1
    return words


def _encrypt_block(block, words):
    state = bytearray(block)

    def add_round(round_index):
        for i in range(16):
            state[i] ^= words[round_index * 4 + i // 4][i % 4]

    def sub_bytes():
        for i in range(16):
            state[i] = SBOX[state[i]]

    def shift_rows():
        rows = [state[r::4] for r in range(4)]
        for r in range(1, 4):
            rows[r] = rows[r][r:] + rows[r][:r]
        for r in range(4):
            for c in range(4):
                state[r + 4 * c] = rows[r][c]

    def mix_columns():
        for c in range(4):
            col = state[4 * c : 4 * c + 4]
            state[4 * c] = _mul(col[0], 2) ^ _mul(col[1], 3) ^ col[2] ^ col[3]
            state[4 * c + 1] = col[0] ^ _mul(col[1], 2) ^ _mul(col[2], 3) ^ col[3]
            state[4 * c + 2] = col[0] ^ col[1] ^ _mul(col[2], 2) ^ _mul(col[3], 3)
            state[4 * c + 3] = _mul(col[0], 3) ^ col[1] ^ col[2] ^ _mul(col[3], 2)

    add_round(0)
    for round_index in range(1, 14):
        sub_bytes()
        shift_rows()
        mix_columns()
        add_round(round_index)
    sub_bytes()
    shift_rows()
    add_round(14)
    return bytes(state)


def _self_test():
    key = bytes(range(32))
    plain = bytes.fromhex("00112233445566778899aabbccddeeff")
    words = _expand(key)
    cipher = _encrypt_block(plain, words)
    expect = bytes.fromhex("8ea2b7ca516745bfeafc49904b496089")
    if cipher != expect:
        raise RuntimeError("AES 自检失败")


_self_test()


def derive(master):
    enc_key = hmac.new(master, b"enc", hashlib.sha256).digest()
    mac_key = hmac.new(master, b"mac", hashlib.sha256).digest()
    return enc_key, mac_key


def encrypt(master, plain):
    enc_key, mac_key = derive(master)
    words = _expand(enc_key)
    nonce = os.urandom(16)
    counter = int.from_bytes(nonce, "big")
    out = bytearray()
    for offset in range(0, len(plain), 16):
        block = _encrypt_block(counter.to_bytes(16, "big"), words)
        chunk = plain[offset : offset + 16]
        out.extend(a ^ b for a, b in zip(chunk, block))
        counter = (counter + 1) & ((1 << 128) - 1)
    ciphertext = bytes(out)
    tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
    return nonce + tag + ciphertext


def decrypt(master, blob):
    if len(blob) < 48:
        raise ValueError("密文太短")
    enc_key, mac_key = derive(master)
    nonce, tag, ciphertext = blob[:16], blob[16:48], blob[48:]
    expect = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expect):
        raise ValueError("密文校验失败")
    words = _expand(enc_key)
    counter = int.from_bytes(nonce, "big")
    out = bytearray()
    for offset in range(0, len(ciphertext), 16):
        block = _encrypt_block(counter.to_bytes(16, "big"), words)
        chunk = ciphertext[offset : offset + 16]
        out.extend(a ^ b for a, b in zip(chunk, block))
        counter = (counter + 1) & ((1 << 128) - 1)
    return bytes(out)
