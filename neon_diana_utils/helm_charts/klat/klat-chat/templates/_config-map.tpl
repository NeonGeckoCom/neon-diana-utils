{{- define "klat_config.configmap"}}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ tpl .Values.klat.configMap . }}
data:
  "klat.yaml": |
    {{  tpl .Values.klat.klatConfig . | nindent 4}}
{{- end -}}