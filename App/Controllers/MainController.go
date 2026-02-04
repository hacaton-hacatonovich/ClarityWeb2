package Controllers

import (
	"ClarityWeb/App/Controllers/Base"
	"html/template"
	"net/http"
)

func ShowMainPage(w http.ResponseWriter, r *http.Request) {
	data := struct {
		Title string
	}{
		Title: "Мой сайт",
	}
	path := Base.GetAbsolutPath("views")
	tmpl, err := template.ParseFiles(path+"main_page.html", path+"templates/header.html")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	err = tmpl.Execute(w, data)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func ShowModificationPortfolioPage(w http.ResponseWriter, r *http.Request) {
	data := struct {
		Title string
	}{
		Title: "Мой сайт",
	}
	path := Base.GetAbsolutPath("views")
	tmpl, err := template.ParseFiles(path + "portfolio_update.html")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	err = tmpl.Execute(w, data)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
