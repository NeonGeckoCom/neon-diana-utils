{{- define "base-neon.deployment" -}}

apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ default .Chart.Name .Values.serviceName }}
spec:
  replicas:  {{ .Values.replicaCount }}
  selector:
    matchLabels:
      neon.diana.service: {{ default .Chart.Name .Values.serviceName }}
  strategy:
    type: Recreate
  template:
    metadata:
      annotations:
        releaseTime: {{ dateInZone "2006-01-02 15:04:05Z" (now) "UTC"| quote }}
      labels:
        neon.diana.service: {{ default .Chart.Name .Values.serviceName }}
        neon.project.name: neon
        neon.service.class: neon-core
    spec:
      restartPolicy: Always
      containers:
        - image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          name: {{ default .Chart.Name .Values.serviceName }}
          volumeMounts:
            - name: config
              mountPath: /config/neon/neon.yaml
              subPath: neon.yaml
            {{- if .Values.persistentVolumeClaim }}
            - mountPath: {{ .Values.persistentVolumeClaim.containerPath }}
              name: {{ .Values.persistentVolumeClaim.name }}
            {{- end -}}
          {{- if .Values.resources }}
          resources:
          {{- toYaml $.Values.resources | nindent 12 -}}
          {{ end }}
          {{- if .Values.env }}
          env:
          {{- toYaml $.Values.env | nindent 12 -}}
          {{ end }}
      volumes:
        - name: config
          projected:
            sources:
              - configMap:
                  name: {{ .Values.configMap }}
        {{- if .Values.persistentVolumeClaim }}
        - name: {{ .Values.persistentVolumeClaim.name }}
          persistentVolumeClaim:
            claimName: {{ .Values.persistentVolumeClaim.claimName }}
        {{- end -}}
{{- end -}}