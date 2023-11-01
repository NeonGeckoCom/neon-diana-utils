{{- define "diana_config.secret"}}
apiVersion: v1
kind: Secret
metadata:
  name: {{ tpl .Values.backend.configSecret . }}
type: Opaque
data:
  "diana.yaml": |-
    {{ tpl .Values.backend.dianaConfig . }}
{{- end -}}