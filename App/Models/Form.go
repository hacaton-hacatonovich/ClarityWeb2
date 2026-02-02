package Models

import "time"

type Form struct {
	Name      string    `json:"name"`
	Company   string    `json:"company"`
	Phone     string    `json:"Phone"`
	Message   string    `json:"message"`
	Topics    []string  `json:"topics"`
	Theme     string    `json:"theme"`
	Colors    []string  `json:"colors"`
	Links     []string  `json:"links"`
	ID        string    `json:"id"`
	Timestamp time.Time `json:"timestamp"`
}
