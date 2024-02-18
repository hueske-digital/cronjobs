import docker
import os
import logging
import sys

# Konfiguriere das Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Umgebungsvariablen
CRON_CONTAINER_NAME = os.getenv("CRON_CONTAINER_NAME", "cron")
RESTART_LABEL = "ofelia.restart"
STACK_LABEL = "com.docker.compose.project"

try:
    # Verbindung zum Docker-Client herstellen
    client = docker.from_env()
except docker.errors.DockerException as e:
    logging.error("Fehler beim Verbinden mit dem Docker Daemon: %s", e)
    sys.exit(1)

# Speichert die IDs der bereits neugestarteten Stacks
restarted_stacks = set()

def restart_cron_container(compose_project):
    """
    Startet den Cron-Container innerhalb des angegebenen Compose-Stacks neu.
    """
    global restarted_stacks

    # Überprüfe, ob der Stack bereits behandelt wurde
    if compose_project in restarted_stacks:
        return

    try:
        for container in client.containers.list(all=True, filters={"label": f"{STACK_LABEL}={compose_project}"}):
            labels = container.labels
            if container.name == CRON_CONTAINER_NAME:
                logging.info(f"Neustart des Containers: {container.name}")
                container.restart()
                restarted_stacks.add(compose_project)
                break
    except docker.errors.DockerException as e:
        logging.error("Fehler beim Neustarten des Containers: %s", e)

def handle_start_event(event):
    """
    Verarbeitet Container-Start-Events.
    """
    attributes = event['Actor']['Attributes']
    compose_project = attributes.get(STACK_LABEL)
    restart_label = attributes.get(RESTART_LABEL)

    # Wenn das Label gesetzt ist und zum ersten Mal in diesem Stack
    if restart_label == "true" and compose_project and compose_project not in restarted_stacks:
        restart_cron_container(compose_project)

def listen_for_container_starts():
    """
    Registriert ein Event-Listener, um auf Container-Start-Events zu hören.
    """
    try:
        for event in client.events(decode=True, filters={"event": "start"}):
            handle_start_event(event)
    except docker.errors.DockerException as e:
        logging.error("Fehler beim Abhören von Docker Events: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    logging.info("Lausche auf startende Container...")
    listen_for_container_starts()
