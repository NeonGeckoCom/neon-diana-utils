{{- define "service.domain" -}}
{{- printf "%s.%s" .Values.subdomain .Values.domain -}}
{{- end }}