{{- define "fasterwhisper_config.configmap"}}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ tpl .Values.core.configMap . }}
data:
  "mycroft.conf": |
    {{ tpl .Values.core.fasterwhisperConfig . | nindent 4}}
{{- end -}}