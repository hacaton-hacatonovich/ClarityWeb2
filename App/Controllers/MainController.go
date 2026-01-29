package Controllers

import (
	"ClarityWeb/App/Controllers/Base"
	"fmt"
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
	tpl, err := template.ParseFiles(path+"main_page.html", path+"templates/header.html")
	fmt.Println(path + "main_page.html")
	fmt.Println(path + "templates/header.html")
	if err != nil {

	}
	err = tpl.Execute(w, data)
}
