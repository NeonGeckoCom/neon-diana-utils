{{- define "base-mq.deployment" -}}

apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ tpl .Chart.Name . }}
spec:
  replicas:  {{ tpl .Values.replicaCount . }}
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
        neon.service.class: mq-backend
    spec:
      restartPolicy: Always
      containers:
        - image: {{ tpl .Values.image.repository . }}:{{ tpl .Values.image.tag . }}
          name: {{ tpl .Chart.Name . }}
          volumeMounts:
            - mountPath: /config
            name: config
      volumes:
        - name: config
          projected:
            sources:
              - secret:
                  name: {{ tpl .Values.configSecret }}
{{- end -}}