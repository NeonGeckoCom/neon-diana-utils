{{- define "base-neon.service" -}}
apiVersion: v1
kind: Service
metadata:
  labels:
    neon.project.name: neon
    neon.diana.service: {{ .Chart.Name }}
    neon.service.class: neon-core
  name: {{ .Chart.Name }}
spec:
  clusterIP: None
  selector:
    neon.diana.service: {{ .Chart.Name }}
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
{{- end -}}
