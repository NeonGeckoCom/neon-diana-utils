{{- define "diana_rabbitmq.secret" -}}
apiVersion: v1
kind: Secret
metadata:
  name: {{ tpl .Values.backend.rabbitmq.loadDefinition.existingSecret . }}
type: Opaque
data:
  "load_definition.json": |-
    {{ tpl .Values.backend.rabbitMqConfig . }}
{{- end -}}