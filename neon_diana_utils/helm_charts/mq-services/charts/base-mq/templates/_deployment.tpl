{{- define "base-mq.deployment" -}}

apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Chart.Name }}
spec:
  replicas:  {{ .Values.replicaCount }}
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
        neon.service.class: mq-backend
    spec:
      restartPolicy: Always
      containers:
        - image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          name: {{ .Chart.Name }}
          volumeMounts:
            - mountPath: /config/neon
              name: config
      volumes:
        - name: config
          projected:
            sources:
              - secret:
                  name: {{ .Values.configSecret }}
        {{- if .Values.persistentVolumeClaim }}
        - name: {{ .Values.persistentVolumeClaim.name }}
          persistentVolumeClaim:
            claimName: {{ .Values.persistentVolumeClaim.claimName }}
        {{- end -}}
      {{- if .Values.image.pullSecret }}
      imagePullSecrets:
        - name: {{ .Values.image.pullSecret }}
      {{- end -}}
{{- end -}}