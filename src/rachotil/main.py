import paramiko
from ssh.connection import host, user, password


def main():
    print("--- RACHOTIL TERMINAL ---")
    print(f"Připojování k {user}@{host}...")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname=host, username=user, password=password, timeout=10)
        print("Spojení navázáno! Napiš 'exit' pro ukončení.\n")

        while True:
            prikaz = input(f"{user}@{host}:~$ ")

            if prikaz.lower() in ["exit", "quit"]:
                break

            if not prikaz.strip():
                continue

            stdin, stdout, stderr = client.exec_command(prikaz)
            vystup = stdout.read().decode()
            chyby = stderr.read().decode()

            if vystup:
                print(vystup, end="")
            if chyby:
                print(f"CHYBA: {chyby}", end="")

    except Exception as e:
        print(f"\nCHYBA PŘIPOJENÍ: {e}")
        print("Ujisti se, že máš zapnutou VPN!")
    finally:
        client.close()
        print("\nSpojení ukončeno.")


if __name__ == "__main__":
    main()