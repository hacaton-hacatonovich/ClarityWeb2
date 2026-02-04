package Errors

import (
	"ClarityWeb/App/Controllers/Base"
	"fmt"
	"log"
	"os"
)

func ErrorController(error_type string) {
	file, err := os.OpenFile(Base.GetAbsolutPath("logs")+"error_30.01.2026.log", os.O_WRONLY|os.O_CREATE|os.O_APPEND, 0777)
	if err != nil {
		fmt.Println(err)
	}
	fmt.Println(file.Name())
	defer file.Close()
	log.SetOutput(file)
	switch error_type {
	case "database_connection_error":
		log.Printf("database connection error")
	}
}
