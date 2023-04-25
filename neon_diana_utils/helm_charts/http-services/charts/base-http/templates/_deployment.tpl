{{- define "base-http.deployment" -}}

apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ tpl .Chart.Name . }}
spec:
  replicas: 1
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
        neon.service.class: http
    spec:
      containers:
        - image: {{ tpl .Values.image.repository . }}:{{ tpl .Values.image.tag . }}
          name: {{ tpl .Chart.Name . }}
          ports:
            - name: {{ tpl .Values.service_name . }}
              containerPort: {{ tpl .Values.service_port . }}
              protocol: TCP
      restartPolicy: Always
{{- end -}}