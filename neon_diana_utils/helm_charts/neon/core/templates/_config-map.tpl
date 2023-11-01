{{- define "neon_config.configmap"}}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ tpl .Values.core.configMap . }}
data:
  "neon.yaml": |
    {{ tpl .Values.core.neonConfig . | nindent 4}}
{{- end -}}