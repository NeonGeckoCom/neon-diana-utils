{{- define "base-mq.service" -}}
apiVersion: v1
kind: Service
metadata:
  labels:
    neon.project.name: diana
    neon.diana.service: {{ tpl .Chart.Name . }}
    neon.service.class: mq-backend
  name: {{ tpl .Chart.Name . }}
spec:
  clusterIP: None
  ports:
    - name: headless
      port: 55555
      targetPort: 0
  selector:
    neon.diana.service: {{ tpl .Chart.Name . }}
{{- end -}}
