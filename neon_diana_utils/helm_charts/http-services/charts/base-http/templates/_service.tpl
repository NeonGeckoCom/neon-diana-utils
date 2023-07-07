{{- define "base-http.service" -}}
apiVersion: v1
kind: Service
metadata:
  labels:
    neon.project.name: diana
    neon.diana.service: {{ tpl .Chart.Name . }}
    neon.service.class: http-backend
  name: {{ .Chart.Name }}
spec:
  type: ClusterIP
  ports:
    - name: {{ .Chart.Name }}
      port: {{ .Values.servicePort }}
      targetPort: {{ .Values.service.targetPort }}
      protocol: TCP
  selector:
    neon.diana.service: {{ .Chart.Name }}
{{- end -}}
