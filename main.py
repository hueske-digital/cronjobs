import docker, os
from docker.errors import APIError, NotFound

label_key = "ofelia.enabled"
label_value = "true"

container_name_to_restart = os.getenv('CONTAINER_NAME_TO_RESTART')
if not container_name_to_restart:
    print("Die Umgebungsvariable 'CONTAINER_NAME_TO_RESTART' muss gesetzt sein.")
    exit(1)

client = docker.from_env()

def restart_container(container_name):
    try:
        container = client.containers.get(container_name)
        container.restart()
        print(f"Container {container_name} wurde neu gestartet.")
    except NotFound:
        print(f"Container {container_name} nicht gefunden.")
    except APIError as e:
        print(f"API Fehler beim Neustarten des Containers {container_name}: {e}")

def handle_event(event):
    if event.get("Type") == "container" and event.get("Action") == "start":
        container_id = event.get("Actor").get("ID")
        try:
            container = client.containers.get(container_id)
            labels = container.labels
            if labels.get(label_key) == label_value:
                print(f"Container mit Label {label_key}:{label_value} gestartet: {container.name}")
                restart_container(container_name_to_restart)
        except NotFound:
            print(f"Container {container_id} nicht gefunden.")
        except APIError as e:
            print(f"API Fehler beim Abrufen des Containers {container_id}: {e}")

def main():
    print("Skript läuft und hört auf Container-Ereignisse...")
    try:
        for event in client.events(decode=True):
            handle_event(event)
    except Exception as e:
        print(f"Unbekannter Fehler: {e}")

if __name__ == "__main__":
    main()
