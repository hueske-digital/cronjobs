package main

import (
	"context"
	"fmt"
	"os"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/filters"
	"github.com/docker/docker/api/types/events"
	"github.com/docker/docker/client"
)

func main() {
	ctx := context.Background()
	cli, err := client.NewEnvClient()
	if err != nil {
		panic(err)
	}

	labelKey := os.Getenv("LABEL_KEY")
	if labelKey == "" {
		labelKey = "ofelia.restart"
	}

	labelValue := os.Getenv("LABEL_VALUE")
	if labelValue == "" {
		labelValue = "true"
	}

	containerNameToRestart := os.Getenv("CRON_CONTAINER")
	if containerNameToRestart == "" {
		containerNameToRestart = "cronjobs-cron-1"
	}

	fmt.Println("Listening on container start events...")

	events, errs := cli.Events(ctx, types.EventsOptions{
		Filters: filters.NewArgs(
			filters.Arg("type", "container"),
			filters.Arg("event", "start"),
		),
	})

	for {
		select {
		case event := <-events:
			handleEvent(ctx, cli, event, labelKey, labelValue, containerNameToRestart)
		case err := <-errs:
			fmt.Printf("Error receiving Docker events: %v\n", err)
			return
		}
	}
}

func handleEvent(ctx context.Context, cli *client.Client, event types.EventsMessage, labelKey, labelValue, containerNameToRestart string) {
	if event.Type == "container" && event.Action == "start" {
		container, err := cli.ContainerInspect(ctx, event.Actor.ID)
		if err != nil {
			fmt.Printf("Error inspecting container %s: %v\n", event.Actor.ID, err)
			return
		}

		if container.Config.Labels[labelKey] == labelValue {
			fmt.Printf("Container with label %s:%s started: %s\n", labelKey, labelValue, container.Name)
			restartContainer(ctx, cli, containerNameToRestart)
		}
	}
}

func restartContainer(ctx context.Context, cli *client.Client, containerName string) {
	err := cli.ContainerRestart(ctx, containerName, &container.StopOptions{})
	if err != nil {
		fmt.Printf("Error restarting container %s: %v\n", containerName, err)
	} else {
		fmt.Printf("Container %s was restarted.\n", containerName)
	}
}
