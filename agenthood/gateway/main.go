package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
)

var ctx = context.Background()

type TaskRequest struct {
	Prompt string `json:"prompt"`
}

type TaskResponse struct {
	TaskID string `json:"task_id"`
	Status string `json:"status"`
}

func main() {
	redisUrl := os.Getenv("REDIS_URL")
	if redisUrl == "" {
		redisUrl = "redis://redis:6379/0"
	}
	opts, err := redis.ParseURL(redisUrl)
	if err != nil {
		log.Fatalf("Failed to parse Redis URL: %v", err)
	}
	rdb := redis.NewClient(opts)

	http.HandleFunc("/api/tasks", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Only POST allowed", http.StatusMethodNotAllowed)
			return
		}

		var req TaskRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "Bad Request", http.StatusBadRequest)
			return
		}

		taskID := uuid.New().String()

		// Publish to Redis (The Nervous System)
		err = rdb.XAdd(ctx, &redis.XAddArgs{
			Stream: "task_queue",
			Values: map[string]interface{}{
				"task_id": taskID,
				"prompt":  req.Prompt,
			},
		}).Err()

		if err != nil {
			log.Printf("Failed to publish to Redis: %v", err)
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		}

		log.Printf("Received task %s: %s", taskID, req.Prompt)

		// Reply instantly to the user (Non-Blocking)
		resp := TaskResponse{
			TaskID: taskID,
			Status: "Task Queued. The Python Swarm will pick this up immediately.",
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	})

	log.Println("Go Receptionist starting on port 8080...")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatal(err)
	}
}
