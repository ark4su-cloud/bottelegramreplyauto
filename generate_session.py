from telethon import TelegramClient
from telethon.sessions import StringSession
import config

print("=" * 60)
print(" GENERATOR SESIUNE SECURIZATA (STRING SESSION)")
print("=" * 60)
print("Acest script va genera un cod text unic de conectare.")
print("Acest cod va fi pus in setarile Render, astfel incat serverul sa nu piarda niciodata conexiunea.")
print("-" * 60)

with TelegramClient(StringSession(), config.API_ID, config.API_HASH) as client:
    session_str = client.session.save()
    print("\n" + "=" * 60)
    print("COPIAZA CODUL DE MAI JOS SI TRIMITE-MI-L IN CHAT:")
    print("=" * 60)
    print(session_str)
    print("=" * 60 + "\n")
