import requests
import time
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

SLACK_TOKEN = os.getenv("SLACK_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")


headers = {
    "Authorization": f"Bearer {SLACK_TOKEN}"
}

HISTORY_URL = "https://slack.com/api/conversations.history"
REPLIES_URL = "https://slack.com/api/conversations.replies"


def format_ts(ts):
    return datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M:%S")


def to_unix(dt_str):
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").timestamp()


def slack_get(url, params, max_retries=10):
    for _ in range(max_retries):
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            print(f"Rate limit HTTP 429 em {url}. Esperando {retry_after}s...")
            time.sleep(retry_after)
            continue

        data = response.json()

        if not data.get("ok") and data.get("error") == "ratelimited":
            retry_after = int(response.headers.get("Retry-After", "60"))
            print(f"Rate limit no corpo em {url}. Esperando {retry_after}s...")
            time.sleep(retry_after)
            continue

        return data

    raise RuntimeError(f"Max retries excedido para {url}")


def get_thread_replies(thread_ts):
    params = {
        "channel": CHANNEL_ID,
        "ts": thread_ts
    }

    data = slack_get(REPLIES_URL, params)

    if data.get("ok"):
        return data.get("messages", [])[1:]  # remove a mensagem pai
    else:
        print("Erro thread:", data)
        return []


def export_period(start_dt, end_dt, filename):
    start_ts = to_unix(start_dt)
    end_ts = to_unix(end_dt)

    cursor = None
    total_msgs = 0

    print(f"\nExportando {start_dt} até {end_dt} -> {filename}")

    with open(filename, "w", encoding="utf-8") as f:
        while True:
            params = {
                "channel": CHANNEL_ID,
                "limit": 200,
                "oldest": str(start_ts),
                "latest": str(end_ts),
                "inclusive": True
            }

            if cursor:
                params["cursor"] = cursor

            data = slack_get(HISTORY_URL, params)

            if not data.get("ok"):
                print("Erro history:", data)
                break

            messages = data.get("messages", [])

            if not messages and not cursor:
                f.write(f"Nenhuma mensagem encontrada no período {start_dt} até {end_dt}\n")

            # inverte para escrever do mais antigo para o mais novo dentro da página
            messages.reverse()

            for msg in messages:
                text = msg.get("text", "")
                user = msg.get("user", "BOT/UNKNOWN")
                ts = msg.get("ts")

                f.write("==================================================\n")
                f.write(f"🕒 {format_ts(ts)}\n")
                f.write(f"👤 {user}\n")
                f.write(f"💬 {text}\n")

                # busca replies da thread
                if msg.get("reply_count", 0) > 0:
                    replies = get_thread_replies(ts)

                    for reply in replies:
                        r_ts = reply.get("ts")
                        r_ts_float = float(r_ts)

                        # filtra replies para o mesmo período do arquivo
                        if start_ts <= r_ts_float <= end_ts:
                            r_text = reply.get("text", "")
                            r_user = reply.get("user", "BOT/UNKNOWN")
                            f.write(f"   ↳ [{format_ts(r_ts)}] {r_user}: {r_text}\n")

                total_msgs += 1
                time.sleep(0.3)

            cursor = data.get("response_metadata", {}).get("next_cursor")

            if not cursor:
                break

            time.sleep(1)

    print(f"✅ Arquivo salvo: {filename} | mensagens principais exportadas: {total_msgs}")


periods = [
    ("2026-01-01 00:00:00", "2026-06-30 23:59:59", "mensagens_2026_S1.txt"),
    ("2025-07-01 00:00:00", "2025-12-31 23:59:59", "mensagens_2025_S2.txt"),
    ("2025-01-01 00:00:00", "2025-06-30 23:59:59", "mensagens_2025_S1.txt"),
    ("2024-07-01 00:00:00", "2024-12-31 23:59:59", "mensagens_2024_S2.txt"),
    ("2024-01-01 00:00:00", "2024-06-30 23:59:59", "mensagens_2024_S1.txt"),
    ("2023-07-01 00:00:00", "2023-12-31 23:59:59", "mensagens_2023_S2.txt"),
    ("2023-01-01 00:00:00", "2023-06-30 23:59:59", "mensagens_2023_S1.txt"),
]

for start_dt, end_dt, filename in periods:
    export_period(start_dt, end_dt, filename)

print("\n✅ Exportação concluída.")