{{- define "cbf_config.configmap"}}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ tpl .Values.chatbots.configMap . }}
data:
  "{{ tpl .Values.chatbots.configFilename . }}": |
    {{  tpl .Values.chatbots.cbfConfig . | nindent 4}}
{{- end -}}