{{- define "base-mq.deployment" -}}
{{- $fullName := default .Chart.Name  .Values.serviceName -}}

apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ $fullName }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      neon.diana.service: {{ $fullName }}
  strategy:
    type: Recreate
  template:
    metadata:
      annotations:
        releaseTime: {{ dateInZone "2006-01-02 15:04:05Z" (now) "UTC"| quote }}
      labels:
        neon.diana.service: {{ $fullName }}
        neon.project.name: diana
        neon.service.class: mq-backend
    spec:
      restartPolicy: Always
      containers:
        - image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          name: {{ $fullName }}
          volumeMounts:
            - mountPath: /config/neon
              name: config
            {{- if .Values.persistentVolumeClaim }}
            - mountPath: {{ .Values.persistentVolumeClaim.containerPath }}
              name: {{ .Values.persistentVolumeClaim.name }}
            {{- end -}}
          {{- if .Values.resources }}
          resources:
          {{- toYaml $.Values.resources | nindent 12 -}}
          {{ end }}
      volumes:
        - name: config
          projected:
            sources:
            {{- if .Values.configSecrets }}
            {{- range .Values.configSecrets }}
              - secret:
                  name: {{ . }}
            {{- end }}
            {{ else }}
              - secret:
                  name: {{ .Values.configSecret }}
            {{- end }}
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