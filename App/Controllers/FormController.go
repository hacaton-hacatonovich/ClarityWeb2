package Controllers

import (
	"ClarityWeb/App/Controllers/Base"
	"ClarityWeb/App/Models"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

func FormProcessing(w http.ResponseWriter, r *http.Request) {
	if r.Method == "POST" {

		// Декодируем JSON из тела запроса
		var formData Models.Form
		decoder := json.NewDecoder(r.Body)
		decoder.DisallowUnknownFields()

		if err := decoder.Decode(&formData); err != nil {
			http.Error(w, "Ошибка JSON: "+err.Error(), http.StatusBadRequest)
			return
		}

		// Добавляем timestamp если не указан
		if formData.Timestamp.IsZero() {
			formData.Timestamp = time.Now()
		}
		WriteToFile(formData)

	}
}

func WriteToFile(form Models.Form) {
	filename := Base.GetAbsolutPath("applications")
	if dir := filepath.Dir(filename); dir != "" {
		if err := os.MkdirAll(dir, 0755); err != nil {
		}
	}

	// Добавляем ID и timestamp если нужно
	if form.Timestamp.IsZero() {
		form.Timestamp = time.Now()
	}
	if form.ID == "" {
		form.ID = fmt.Sprintf("form_%d", time.Now().UnixNano())
	}

	// Читаем существующие данные
	var forms []Models.Form

	// Проверяем, существует ли файл
	if _, err := os.Stat(filename); err == nil {
		// Файл существует, читаем его
		data, err := os.ReadFile(filename)
		if err != nil {
		}

		// Пытаемся распарсить JSON
		if len(data) > 0 {
			// Удаляем возможные пробелы в начале и конце
			dataStr := strings.TrimSpace(string(data))

			// Проверяем, начинается ли с '['
			if strings.HasPrefix(dataStr, "[") && strings.HasSuffix(dataStr, "]") {
				if err := json.Unmarshal([]byte(dataStr), &forms); err != nil {
					// Если ошибка парсинга, начинаем новый массив
					forms = []Models.Form{}
				}
			} else {
				// Если не массив JSON, начинаем новый
				forms = []Models.Form{}
			}
		}
	}

	// Добавляем новую форму в массив
	forms = append(forms, form)

	// Кодируем обратно в JSON с красивым форматированием
	jsonData, err := json.MarshalIndent(forms, "", "  ")
	if err != nil {

	}

	// Записываем в файл (перезаписываем полностью)
	if err := os.WriteFile(filename, jsonData, 0644); err != nil {

	}

}
