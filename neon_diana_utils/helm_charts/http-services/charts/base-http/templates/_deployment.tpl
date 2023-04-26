{{- define "base-http.deployment" -}}

apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Chart.Name }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      neon.diana.service: {{ .Chart.Name }}
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        neon.diana.service: {{ .Chart.Name }}
        neon.project.name: diana
        neon.service.class: http-backend
    spec:
      containers:
        - image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
          name: {{ .Chart.Name }}
          ports:
            - name: {{ .Chart.Name }}
              containerPort: {{ .Values.servicePort }}
              protocol: TCP
      restartPolicy: Always
{{- end -}}