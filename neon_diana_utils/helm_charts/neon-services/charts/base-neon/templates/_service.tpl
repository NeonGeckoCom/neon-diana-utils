{{- define "base-mq.service" -}}
apiVersion: v1
kind: Service
metadata:
  labels:
    neon.project.name: diana
    neon.diana.service: {{ .Chart.Name }}
    neon.service.class: mq-backend
  name: {{ .Chart.Name }}
spec:
  clusterIP: None
  ports:
    - name: headless
      port: 55555
      targetPort: 0
    {{- if .Values.port }}
    - name: {{ .Values.port.name }}
      port: {{ .Values.port.number }}
      targetPort: {{ .Values.port.targetPort }}
      protocol: TCP
    {{- end -}}
  selector:
    neon.diana.service: {{ .Chart.Name }}
{{- end -}}
