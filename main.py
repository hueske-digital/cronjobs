import docker
import os
import logging
import sys

# Konfiguriere das Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Umgebungsvariablen
CRON_CONTAINER_NAME = os.getenv("CRON_CONTAINER_NAME", "cron")
LISTENER_LABEL_VALUE = os.getenv("LISTENER_LABEL_VALUE", "listener_container")
LISTENER_LABEL_KEY = "com.docker.compose.service"

try:
    # Verbindung zum Docker-Client herstellen
    client = docker.from_env()
except docker.errors.DockerException as e:
    logging.error("Fehler beim Verbinden mit dem Docker Daemon: %s", e)
    sys.exit(1)

def get_current_stack_name():
    """
    Ermittelt den Namen des Compose-Stacks, in dem sich der Listener befindet.
    """
    try:
        current_container_id = os.getenv("HOSTNAME")
        container = client.containers.get(current_container_id)
        return container.labels.get("com.docker.compose.project")
    except docker.errors.DockerException as e:
        logging.error("Fehler beim Ermitteln des aktuellen Compose-Stacks: %s", e)
        sys.exit(1)

def restart_cron_container(current_stack_name):
    """
    Startet den Cron-Container im aktuellen Compose-Stack neu.
    """
    try:
        for container in client.containers.list(all=True, filters={"label": f"com.docker.compose.project={current_stack_name}"}):
            if container.labels.get(LISTENER_LABEL_KEY) == CRON_CONTAINER_NAME:
                logging.info(f"Neustart des 'Cron'-Containers im Stack '{current_stack_name}'.")
                container.restart()
                break
    except docker.errors.DockerException as e:
        logging.error("Fehler beim Neustarten des 'Cron'-Containers: %s", e)

def listen_for_container_starts():
    """
    Registriert ein Event-Listener, um auf Container-Start-Events zu hören.
    """
    current_stack_name = get_current_stack_name()
    if not current_stack_name:
        logging.error("Konnte den Namen des aktuellen Compose-Stacks nicht ermitteln.")
        return

    logging.info(f"Lausche auf startende Container im Stack '{current_stack_name}'...")
    try:
        for event in client.events(decode=True, filters={"event": "start"}):
            event_stack_name = event['Actor']['Attributes'].get('com.docker.compose.project')
            if event_stack_name == current_stack_name:
                # Überprüft, ob der gestartete Container das spezifische Label hat
                if event['Actor']['Attributes'].get('ofelia.restart') == 'true':
                    restart_cron_container(current_stack_name)
    except docker.errors.DockerException as e:
        logging.error("Fehler beim Abhören von Docker Events: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    listen_for_container_starts()
