{{- define "base-http.service" -}}
apiVersion: v1
kind: Service
metadata:
  labels:
    neon.project.name: diana
    neon.diana.service: {{ tpl .Chart.Name . }}
    neon.service.class: http
  name: {{ tpl .Chart.Name . }}
spec:
  type: ClusterIP
  ports:
    - name: {{ tpl .Chart.Name . }}
      port: {{ tpl .Values.service_port . }}
      targetPort: {{ tpl .Values.service.targetPort . }}
      protocol: TCP
  selector:
    neon.diana.service: {{ tpl .Chart.Name . }}
{{- end -}}
