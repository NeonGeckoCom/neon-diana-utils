{{- define "base-http.deployment" -}}

apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ tpl .Chart.Name . }}
spec:
  replicas: {{ tpl .Values.replicaCount . }}
  selector:
    matchLabels:
      neon.diana.service: {{ tpl .Chart.Name . }}
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        neon.diana.service: {{ tpl .Chart.Name . }}
        neon.project.name: diana
        neon.service.class: http-backend
    spec:
      containers:
        - image: {{ tpl .Values.image.repository . }}:{{ tpl .Values.image.tag . }}
          name: {{ tpl .Chart.Name . }}
          ports:
            - name: {{ tpl .Chart.Name . }}
              containerPort: {{ tpl .Values.servicePort . }}
              protocol: TCP
      restartPolicy: Always
{{- end -}}