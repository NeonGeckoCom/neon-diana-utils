{{ $serviceName := default .Chart.Name .Values.serviceName }}
{{- define "base-neon.service" -}}
apiVersion: v1
kind: Service
metadata:
  labels:
    neon.project.name: neon
    neon.diana.service: {{ $serviceName }}
    neon.service.class: neon-core
  name: {{ $serviceName }}
spec:
  clusterIP: None
  selector:
    neon.diana.service: {{ $serviceName }}
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
