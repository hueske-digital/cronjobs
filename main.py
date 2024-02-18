import docker
import os
from docker.errors import APIError, NotFound

# Umgebungsvariable auslesen
container_name_to_restart = os.getenv('CONTAINER_NAME_TO_RESTART')
if not container_name_to_restart:
    print("Die Umgebungsvariable 'CONTAINER_NAME_TO_RESTART' muss gesetzt sein.")
    exit(1)

label_key = "ofelia.enabled"
label_value = "true"

client = docker.from_env()

def restart_target_container():
    try:
        # Listet alle laufenden Container auf und filtert nach dem Service-Namen
        containers = client.containers.list(filters={"label": f"com.docker.compose.service={container_name_to_restart}"})
        for container in containers:
            container.restart()
            print(f"Container {container.name} wurde erfolgreich neu gestartet.")
            break  # Beendet die Schleife nach dem ersten erfolgreichen Neustart
    except APIError as e:
        print(f"Fehler beim Neustarten des Containers: {e}")

def handle_event(event):
    if event.get("Type") == "container" and event.get("Action") == "start":
        container_id = event.get("Actor").get("ID")
        container = client.containers.get(container_id)
        labels = container.labels

        if labels.get(label_key) == label_value:
            service_name = container.attrs['Config']['Labels'].get('com.docker.compose.service')
            # Überprüft, ob der gestartete Container nicht der Zielcontainer ist
            if service_name != container_name_to_restart:
                print(f"Container {container.name} mit Label {label_key}:{label_value} gestartet.")
                restart_target_container()

def main():
    print("Lausche auf Container-Ereignisse...")
    try:
        for event in client.events(decode=True):
            handle_event(event)
    except Exception as e:
        print(f"Unbekannter Fehler: {e}")

if __name__ == "__main__":
    main()
