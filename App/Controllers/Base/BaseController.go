package Base

import (
	"os"
	"strings"
)

func GetAbsolutPath(format string) string {
	path, _ := os.Getwd()
	sb := strings.Builder{}
	sb.WriteString(path)
	sb.WriteString("/resources/")
	switch format {
	case "views":
		sb.WriteString("views/")
	case "image":
		sb.WriteString("images/")
	}
	return sb.String()
}
