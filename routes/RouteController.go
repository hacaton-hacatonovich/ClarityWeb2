package routes

import (
	"ClarityWeb/App/Controllers"
	"net/http"
)

func Routes() {
	fs := http.FileServer(http.Dir("./resources"))
	http.Handle("/resources/", fs)
	http.HandleFunc("/", Controllers.ShowMainPage)
	http.HandleFunc("/portfolio_modification", Controllers.ShowModificationPortfolioPage)
	http.HandleFunc("/form_processing", Controllers.FormProcessing)
}
