"""SQLite 数据访问：命盘只读，账户资料与会话使用同一数据库。"""
import hashlib, json, os, secrets, sqlite3, time
DB_PATH = os.environ.get("ZIWEI_DB", "/app/data/ziwei.sqlite3")
SESSION_DAYS = 30

def connect():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def get_chart(key: str):
    if not os.path.exists(DB_PATH): return None
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT payload FROM charts WHERE chart_key = ?", (key,)).fetchone()
        return json.loads(row["payload"]) if row else None

def init_auth():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, display_name TEXT NOT NULL, created_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, expires_at INTEGER NOT NULL, created_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, label TEXT NOT NULL, birth_date TEXT NOT NULL, hour INTEGER NOT NULL, gender TEXT NOT NULL, created_at INTEGER NOT NULL, UNIQUE(user_id,label));
        CREATE TABLE IF NOT EXISTS query_history (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, chart_key TEXT NOT NULL, birth_date TEXT NOT NULL, hour INTEGER NOT NULL, gender TEXT NOT NULL, queried_at INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at);
        CREATE INDEX IF NOT EXISTS idx_history_user ON query_history(user_id, queried_at DESC);
        """)

def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
    return f"pbkdf2_sha256$210000${salt.hex()}${digest.hex()}"

def verify_password(password, encoded):
    try:
        _, rounds, salt, digest = encoded.split("$")
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds)).hex()
        return secrets.compare_digest(check, digest)
    except (ValueError, TypeError): return False

def create_user(email, password, display_name):
    with connect() as db:
        cur = db.execute("INSERT INTO users(email,password_hash,display_name,created_at) VALUES(?,?,?,?)", (email,hash_password(password),display_name,int(time.time())))
        return {"id":cur.lastrowid,"email":email,"display_name":display_name}

def authenticate(email, password):
    with connect() as db:
        row=db.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
        return {"id":row["id"],"email":row["email"],"display_name":row["display_name"]} if row and verify_password(password,row["password_hash"]) else None

def create_session(user_id):
    token=secrets.token_urlsafe(32); now=int(time.time())
    with connect() as db:
        db.execute("DELETE FROM sessions WHERE expires_at < ?",(now,)); db.execute("INSERT INTO sessions VALUES(?,?,?,?)",(hashlib.sha256(token.encode()).hexdigest(),user_id,now+SESSION_DAYS*86400,now))
    return token

def user_from_token(token):
    if not token: return None
    with connect() as db:
        row=db.execute("SELECT u.id,u.email,u.display_name FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?",(hashlib.sha256(token.encode()).hexdigest(),int(time.time()))).fetchone()
        return dict(row) if row else None

def delete_session(token):
    if token:
        with connect() as db: db.execute("DELETE FROM sessions WHERE token_hash=?",(hashlib.sha256(token.encode()).hexdigest(),))

def add_history(user_id, key, date, hour, gender):
    with connect() as db:
        db.execute("INSERT INTO query_history(user_id,chart_key,birth_date,hour,gender,queried_at) VALUES(?,?,?,?,?,?)",(user_id,key,date,hour,gender,int(time.time())))
        db.execute("DELETE FROM query_history WHERE user_id=? AND id NOT IN (SELECT id FROM query_history WHERE user_id=? ORDER BY queried_at DESC LIMIT 20)",(user_id,user_id))

def get_user_data(user_id):
    with connect() as db:
        profiles=[dict(x) for x in db.execute("SELECT id,label,birth_date,hour,gender FROM profiles WHERE user_id=? ORDER BY created_at DESC",(user_id,))]
        history=[dict(x) for x in db.execute("SELECT chart_key,birth_date,hour,gender,queried_at FROM query_history WHERE user_id=? ORDER BY queried_at DESC LIMIT 20",(user_id,))]
        return profiles,history

def save_profile(user_id,label,date,hour,gender):
    with connect() as db:
        cur=db.execute("INSERT INTO profiles(user_id,label,birth_date,hour,gender,created_at) VALUES(?,?,?,?,?,?) ON CONFLICT(user_id,label) DO UPDATE SET birth_date=excluded.birth_date,hour=excluded.hour,gender=excluded.gender",(user_id,label,date,hour,gender,int(time.time())))
        return cur.lastrowid

def delete_profile(user_id, profile_id):
    with connect() as db: db.execute("DELETE FROM profiles WHERE id=? AND user_id=?",(profile_id,user_id))
