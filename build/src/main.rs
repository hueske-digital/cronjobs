use bollard::Docker;
use bollard::models::EventMessage;
use bollard::errors::Error as DockerError;
use dotenv::dotenv;
use futures_util::StreamExt;
use std::env;
use std::sync::Arc;
use tokio::sync::Mutex;
use log::{info, debug, error, warn};
use tokio::time::{sleep, Duration};

#[tokio::main]
async fn main() {
    // Lese Umgebungsvariablen (z.B. für LABEL_KEY und LABEL_VALUE)
    dotenv().ok();

    // Setze das Standard-Log-Level auf "info", wenn keine Umgebungsvariable RUST_LOG gesetzt ist
    if env::var("RUST_LOG").is_err() {
        env::set_var("RUST_LOG", "info");
    }

    // Initialisiere den Logger ohne Zeitstempel
    env_logger::Builder::from_default_env()
        .format_timestamp(None)
        .init();

    info!("Listening on container start and stop events...");

    let label_key = env::var("LABEL_KEY").unwrap_or_else(|_| "ofelia.restart".to_string());
    let label_value = env::var("LABEL_VALUE").unwrap_or_else(|_| "true".to_string());
    let container_name_to_restart = env::var("CRON_CONTAINER").unwrap_or_else(|_| "cronjobs-cron-1".to_string());

    let docker = Docker::connect_with_local_defaults().expect("Failed to connect to Docker");

    // Mutex für die Steuerung des Neustart-Timers
    let restart_timer = Arc::new(Mutex::new(None));

    let mut events_stream = docker.events::<String>(None).fuse();

    while let Some(event) = events_stream.next().await {
        match event {
            Ok(event_message) => {
                debug!("Received event: {:?}", event_message);
                let docker = docker.clone();
                let restart_timer = restart_timer.clone();
                let label_key = label_key.clone();
                let label_value = label_value.clone();
                let container_name_to_restart = container_name_to_restart.clone();

                tokio::spawn(async move {
                    handle_event(&docker, event_message, &label_key, &label_value, &container_name_to_restart, restart_timer).await;
                });
            },
            Err(e) => error!("Error receiving event: {:?}", e),
        }
    }
}

async fn handle_event(
    docker: &Docker,
    event: EventMessage,
    label_key: &str,
    label_value: &str,
    container_name_to_restart: &str,
    restart_timer: Arc<Mutex<Option<tokio::task::JoinHandle<()>>>>
) {
    if let Some(action) = event.action {
        if action == "start" || action == "stop" {
            if let Some(actor) = event.actor {
                if let Some(container_id) = actor.id {
                    // Hole den Container-Namen
                    let container_info = docker.inspect_container(&container_id, None).await;
                    if let Ok(container_info) = container_info {
                        if let Some(container_name) = container_info.name {
                            // Ignoriere Events des Cron-Containers selbst
                            if container_name == format!("/{}", container_name_to_restart) {
                                debug!("Ignoring event for the cron container itself: {}", container_name);
                                return;
                            }
                        }
                    }

                    match docker.inspect_container(&container_id, None).await {
                        Ok(container_info) => {
                            if let Some(labels) = container_info.config.and_then(|c| c.labels) {
                                if labels.get(label_key).map_or(false, |v| v == label_value) {
                                    info!("Container {} {}ed", container_info.name.unwrap_or_default(), action);

                                    // Setze den Timer zurück, wenn ein neuer Container startet oder stoppt
                                    let mut timer_guard = restart_timer.lock().await;
                                    if let Some(existing_timer) = timer_guard.take() {
                                        existing_timer.abort(); // Abbrechen des bestehenden Timers
                                        info!("Timer reset for restarting the cron container");
                                    }

                                    let docker = docker.clone();
                                    let container_name_to_restart = container_name_to_restart.to_string();

                                    // Starte einen neuen Timer (z.B. 60 Sekunden)
                                    *timer_guard = Some(tokio::spawn(async move {
                                        info!("Timer set for restarting the cron container in 60 seconds");
                                        sleep(Duration::from_secs(60)).await;
                                        if let Err(e) = restart_container(&docker, &container_name_to_restart).await {
                                            error!("Error restarting container {}: {:?}", container_name_to_restart, e);
                                        }
                                    }));
                                }
                            }
                        },
                        Err(DockerError::DockerResponseServerError { status_code, .. }) if status_code == 404 => {
                            warn!("Container {} not found", container_id);
                        },
                        Err(e) => {
                            error!("API error when getting container {}: {:?}", container_id, e);
                        }
                    }
                }
            }
        }
    }
}

async fn restart_container(docker: &Docker, container_name: &str) -> Result<(), DockerError> {
    match docker.inspect_container(container_name, None).await {
        Ok(_) => {
            docker.restart_container(container_name, None).await?;
            info!("Container {} was restarted.", container_name);
            Ok(())
        },
        Err(DockerError::DockerResponseServerError { status_code, .. }) if status_code == 404 => {
            warn!("Container {} not found.", container_name);
            Ok(())
        },
        Err(e) => {
            error!("API error when restarting container {}: {:?}", container_name, e);
            Err(e)
        }
    }
}