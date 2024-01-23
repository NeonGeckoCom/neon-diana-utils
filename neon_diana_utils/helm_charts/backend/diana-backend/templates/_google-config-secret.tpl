{{- define "google_json.secret"}}
apiVersion: v1
kind: Secret
metadata:
  name: {{ tpl .Values.backend.googleSecret . }}
type: Opaque
data:
  "google.json": |-
    {{ tpl .Values.backend.googleJson . }}
{{- end -}}