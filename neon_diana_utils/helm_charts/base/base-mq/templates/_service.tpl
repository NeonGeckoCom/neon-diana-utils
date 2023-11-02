{{- define "base-mq.service" -}}
{{- $fullName := default .Chart.Name  .Values.serviceName -}}

apiVersion: v1
kind: Service
metadata:
  labels:
    neon.project.name: diana
    neon.diana.service: {{ $fullName }}
    neon.service.class: mq-backend
  name: {{ $fullName }}
spec:
  clusterIP: None
  ports:
    - name: headless
      port: 55555
      targetPort: 0
  selector:
    neon.diana.service: {{ $fullName }}
{{- end -}}
