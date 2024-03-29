{{- define "base-neon.ingress" -}}
{{ if .Values.ingress.enabled }}
{{- $domain := .Values.domain -}}
{{- if semverCompare ">=1.19-0" .Capabilities.KubeVersion.GitVersion -}}
apiVersion: networking.k8s.io/v1
{{- else if semverCompare ">=1.14-0" .Capabilities.KubeVersion.GitVersion -}}
apiVersion: networking.k8s.io/v1beta1
{{- else -}}
apiVersion: extensions/v1beta1
{{- end }}
kind: Ingress
metadata:
  name: ingress-iris-http
  annotations:
    kubernetes.io/ingress.class: {{ .Values.ingress.ingressClassName }}
    cert-manager.io/issuer: {{ .Values.ingress.certIssuer }}
spec:
  tls:
    - secretName: {{ .Values.ingress.tlsSecretName }}
      hosts:
        {{- range .Values.ingress.rules }}
        - {{ printf "%s.%s " .host $.Values.domain }}
        {{- end }}

  rules:
    {{- range .Values.ingress.rules }}
    - host: {{ printf "%s.%s " .host $.Values.domain }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ .serviceName }}
                port:
                  number: {{ .servicePort }}
    {{- end }}

  {{- end -}}
{{- end -}}