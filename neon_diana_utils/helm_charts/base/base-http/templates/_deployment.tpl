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
      annotations:
        releaseTime: {{ dateInZone "2006-01-02 15:04:05Z" (now) "UTC"| quote }}
      labels:
        neon.diana.service: {{ .Chart.Name }}
        neon.project.name: diana
        neon.service.class: http-backend
    spec:
      containers:
        - image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          name: {{ .Chart.Name }}
          ports:
            - name: {{ .Chart.Name }}
              containerPort: {{ .Values.servicePort }}
              protocol: TCP
          {{- if .Values.configSecret }}
          volumeMounts:
            - mountPath: /config/neon
              name: config
      volumes:
        - name: config
          projected:
            sources:
              - secret:
                  name: {{ .Values.configSecret }}
      {{- end }}
      restartPolicy: Always
{{- end -}}