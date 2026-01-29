package routes

import (
	"ClarityWeb/App/Controllers"
	"net/http"
)

func Routes() {
	fs := http.FileServer(http.Dir("/resources"))
	http.Handle("/resources/", http.StripPrefix("/resources", fs))
	http.HandleFunc("/", Controllers.ShowMainPage)

}
