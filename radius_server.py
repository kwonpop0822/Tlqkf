import socket
import sqlite3
import hashlib
import os
from datetime import datetime
from pyrad.packet import AuthPacket, AccessAccept, AccessReject

SECRET = b"testing123"  # 공유기에 입력할 Shared Secret
UDP_PORT = 1812
DB_FILE = "users.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            expire_date TEXT
        )
    ''')
    conn.commit()

    # 테스트 계정 추가 (kwonpop / 1234)
    salt = os.urandom(16).hex()
    hashed = hashlib.pbkdf2_hmac('sha256', "1234".encode('utf-8'), salt.encode('utf-8'), 100000).hex()
    cursor.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?, 1, ?)', ("kwonpop", hashed, salt, "2030-12-31"))
    conn.commit()
    conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash, salt, is_active FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()

    if not row or row[2] != 1:
        return False

    db_hash, salt = row[0], row[1]
    check_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
    return check_hash == db_hash

def start_radius_server():
    init_db()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", UDP_PORT))
    print(f"🔥 무료 호스팅 RADIUS 서버 가동 중! (포트: {UDP_PORT})")

    while True:
        data, addr = sock.recvfrom(1024)
        try:
            req = AuthPacket(packet=data, secret=SECRET)
            username = req.get(1, [b""])[0].decode("utf-8", errors="ignore")
            password = req.get(2, [b""])[0].decode("utf-8", errors="ignore")

            reply = req.CreateReply()
            if verify_user(username, password):
                reply.code = AccessAccept
                print(f"✅ [{username}] 인증 성공!")
            else:
                reply = req.CreateReply()
                reply.code = AccessReject
                print(f"❌ [{username}] 인증 실패!")

            sock.sendto(reply.ReplyPacket(), addr)
        except Exception as e:
            print(f"⚠️ 패킷 처리 에러: {e}")

if __name__ == "__main__":
    start_radius_server()
