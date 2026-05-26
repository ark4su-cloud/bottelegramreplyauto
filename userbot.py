import os
import json
import time
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from telethon import TelegramClient, events
import config

# Calea către fișierul în care ținem minte clienții cărora le-am răspuns deja
REPLIED_USERS_FILE = 'replied_users.json'

# Încărcăm starea anterioară din fișier (dacă există) pentru a nu trimite mesaje repetate
if os.path.exists(REPLIED_USERS_FILE):
    try:
        with open(REPLIED_USERS_FILE, 'r') as f:
            replied_users = json.load(f)
    except Exception:
        replied_users = {}
else:
    replied_users = {}

def save_replied_users():
    try:
        with open(REPLIED_USERS_FILE, 'w') as f:
            json.dump(replied_users, f)
    except Exception as e:
        print(f"[EROARE] Nu s-a putut salva istoricul clienților: {e}")

from telethon import connection

# Inițializăm clientul Telethon (cu conexiune securizată și mascată ConnectionTcpObfuscated pentru a evita blocajele de rețea)
client = TelegramClient('session_personal', config.API_ID, config.API_HASH, connection=connection.ConnectionTcpObfuscated)

@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    # Răspundem doar la mesajele private (excludem grupuri, supergrupuri și canale)
    if not event.is_private:
        return
        
    sender = await event.get_sender()
    if not sender:
        return
        
    sender_id = str(sender.id)
    
    # Nu răspundem dacă ne scriem noi înșine sau dacă mesajul vine de la un alt bot
    if sender.is_self or sender.bot:
        return
        
    # Dacă i-am răspuns deja o dată în trecut, nu îi mai răspundem niciodată automat
    if sender_id in replied_users:
        return
        
    # Verificăm inteligent dacă este un contact mai vechi cu care ai mai vorbit în trecut
    # Citim ultimele 15 mesaje din conversație pentru a vedea dacă ai trimis vreodată vreun mesaj în acest chat
    is_old_contact = False
    try:
        async for msg in client.iter_messages(event.chat_id, limit=15):
            if msg.out:  # msg.out înseamnă că mesajul a fost trimis de tine
                is_old_contact = True
                break
    except Exception as e:
        print(f"[Avertisment] Nu s-a putut citi istoricul pentru {sender_id}: {e}")
        
    if is_old_contact:
        # Dacă ai mai vorbit cu el în trecut, îl salvăm ca fiind procesat și nu îi trimitem nimic
        replied_users[sender_id] = time.time()
        save_replied_users()
        return

    # Dacă a trecut de verificări, înseamnă că este un client 100% NOU care îți scrie prima dată!
    first_name = sender.first_name or "Client"
    username = f" (@{sender.username})" if sender.username else ""
    print(f"[AUTO-REPLY] Client NOU detectat: {first_name}{username}. Trimit mesajul de întâmpinare...")
    
    try:
        # Trimitem răspunsul la mesajul primit
        await event.reply(config.WELCOME_MESSAGE)
        
        # Îl adăugăm definitiv în lista clienților procesați
        replied_users[sender_id] = time.time()
        save_replied_users()
        print(f"[AUTO-REPLY] Mesaj trimis cu succes către clientul nou: {first_name}!")
    except Exception as e:
        print(f"[EROARE] Eșec la trimiterea mesajului: {e}")

class HealthCheckHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running 24/7!")
    
    # Anulam logurile automate in terminal pentru a nu aglomera consola la fiecare ping
    def log_message(self, format, *args):
        return

def start_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"[WEB SERVER] Ruleaza pe portul {port} (pentru pings UptimeRobot)")
    server.serve_forever()

async def main():
    print("=" * 60)
    print(" PORNIRE TELEGRAM USERBOT (AUTO-REPLY CONT PERSONAL)")
    print("=" * 60)
    
    # Pornim serverul web pe un thread separat pentru Render/UptimeRobot
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    
    # Pornește clientul și cere autentificarea dacă este prima rulare
    await client.start(phone=config.PHONE)
    
    me = await client.get_me()
    name = f"{me.first_name} {me.last_name or ''}".strip()
    print(f"\n[SUCCES] Conectat ca: {name} (@{me.username or 'fara_username'})")
    print("[INFO] Botul este activ și ascultă mesajele primite...")
    print("[INFO] Apasă Ctrl+C în terminal pentru a opri botul.")
    print("-" * 60)
    
    # Rulam în fundal și ascultăm mesaje
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n[INFO] Botul a fost oprit manual de către utilizator.")


