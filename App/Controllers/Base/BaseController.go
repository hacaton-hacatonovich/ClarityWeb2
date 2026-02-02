package Base

import (
	"os"
	"strings"
)

func GetAbsolutPath(format string) string {
	path, _ := os.Getwd()
	sb := strings.Builder{}
	sb.WriteString(path)
	switch format {
	case "views":

		sb.WriteString("/resources/views/")
	case "image":

		sb.WriteString("/resources/images/")
	case "default":

		sb.WriteString("/")
	case "logs":
		sb.WriteString("/logs/")
	case "applications":
		sb.WriteString("/storage/files/applications.json")
	}
	return sb.String()
}
