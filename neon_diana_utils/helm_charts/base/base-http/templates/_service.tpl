{{- define "base-http.service" -}}
{{- $fullName := default .Chart.Name .Values.serviceName -}}
apiVersion: v1
kind: Service
metadata:
  labels:
    neon.project.name: diana
    neon.diana.service: {{ $fullName }}
    neon.service.class: http-backend
  name: {{ $fullName }}
spec:
  type: ClusterIP
  ports:
    - name: {{ $fullName }}
      port: {{ .Values.servicePort }}
      targetPort: {{ .Values.service.targetPort }}
      protocol: TCP
  selector:
    neon.diana.service: {{ $fullName }}
{{- end -}}
