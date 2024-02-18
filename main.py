import docker, os
from docker.errors import APIError, NotFound

label_key = os.getenv("LABEL_KEY", "ofelia.restart")
label_value = os.getenv("LABEL_VALUE", "true")
container_name_to_restart = os.getenv("CRON_CONTAINER", "cronjobs-cron-1")

client = docker.from_env()

def restart_container(container_name):
    try:
        container = client.containers.get(container_name)
        container.restart()
        print(f"Container {container_name} was restarted.")
    except NotFound:
        print(f"Container {container_name} not found.")
    except APIError as e:
        print(f"API error when restarting container {container_name}: {e}")

def handle_event(event):
    if event.get("Type") == "container" and event.get("Action") == "start":
        container_id = event.get("Actor").get("ID")
        try:
            container = client.containers.get(container_id)
            labels = container.labels
            if labels.get(label_key) == label_value:
                print(f"Container with label {label_key}:{label_value} started: {container.name}")
                restart_container(container_name_to_restart)
        except NotFound:
            print(f"Container {container_id} not found.")
        except APIError as e:
            print(f"API error when getting container {container_id}: {e}")

def main():
    print("Listening on container start events...")
    try:
        for event in client.events(decode=True):
            handle_event(event)
    except Exception as e:
        print(f"Unknown error: {e}")

if __name__ == "__main__":
    main()
