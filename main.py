import docker
import os
from docker.errors import APIError, NotFound

# Lese den Namen des Containers/Services aus einer Umgebungsvariable
container_name_to_restart = os.getenv('CONTAINER_NAME_TO_RESTART')
if not container_name_to_restart:
    print("Die Umgebungsvariable 'CONTAINER_NAME_TO_RESTART' muss gesetzt sein.")
    exit(1)

label_key = "ofelia.enabled"
label_value = "true"

client = docker.from_env()

def restart_container(container_name):
    try:
        # Filtere Container nach dem Service-Namen
        containers = client.containers.list(filters={"label": f"com.docker.compose.service={container_name}"})
        for container in containers:
            container.restart()
            print(f"Container {container.name} ({container.id}) wurde neu gestartet.")
            return  # Beendet die Schleife nach dem ersten Neustart
    except APIError as e:
        print(f"Fehler beim Neustarten des Containers {container_name}: {e}")

def handle_event(event):
    if event.get("Type") == "container" and event.get("Action") == "start":
        container_id = event.get("Actor").get("ID")
        container = client.containers.get(container_id)
        labels = container.labels

        # Überprüfe, ob der Container das spezifische Label hat und nicht der Container ist, der neu gestartet werden soll
        if labels.get(label_key) == label_value and container.attrs['Config']['Labels'].get('com.docker.compose.service') != container_name_to_restart:
            print(f"Container mit Label {label_key}:{label_value} gestartet: {container.name}")
            restart_container(container_name_to_restart)

def main():
    print("Skript läuft und hört auf Container-Ereignisse...")
    try:
        for event in client.events(decode=True):
            handle_event(event)
    except Exception as e:
        print(f"Unbekannter Fehler: {e}")

if __name__ == "__main__":
    main()
