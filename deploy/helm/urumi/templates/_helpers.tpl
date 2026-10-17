{{- define "urumi.secretName" -}}
{{ default "urumi-secrets" .Values.existingSecret }}
{{- end -}}

{{- define "urumi.publicUrl" -}}
{{ .Values.ingress.scheme }}://{{ .Values.ingress.host }}{{ .Values.ingress.publicPort }}
{{- end -}}

{{- define "urumi.storeUrl" -}}
{{ .Values.ingress.scheme }}://{{ .Values.ingress.storeHost }}{{ .Values.ingress.publicPort }}
{{- end -}}

{{/* Locked-down settings for our own containers (not the third-party images). */}}
{{- define "urumi.podSecurity" -}}
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  runAsGroup: 10001
  seccompProfile:
    type: RuntimeDefault
{{- end -}}

{{- define "urumi.containerSecurity" -}}
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
{{- end -}}

{{/* Settings the gateway, admin API and bootstrap job all share. */}}
{{- define "urumi.backendEnv" -}}
- { name: BIND_HOST, value: "0.0.0.0" }
- { name: POSTGRES_HOST, value: postgres }
- { name: POSTGRES_PORT, value: "5432" }
- { name: POSTGRES_DB, value: gateway }
- { name: POSTGRES_USER, value: gateway }
- name: POSTGRES_PASSWORD
  valueFrom: { secretKeyRef: { name: {{ include "urumi.secretName" . }}, key: POSTGRES_PASSWORD } }
- name: ADMIN_SESSION_SECRET
  valueFrom: { secretKeyRef: { name: {{ include "urumi.secretName" . }}, key: ADMIN_SESSION_SECRET } }
- name: CHAT_GATEWAY_SECRET
  valueFrom: { secretKeyRef: { name: {{ include "urumi.secretName" . }}, key: CHAT_GATEWAY_SECRET } }
# The in-cluster service names of our own MCP servers (for example woocommerce-mcp) skip the private-address check.
- { name: ALLOWED_UPSTREAM_HOSTS, value: "{{ range $i, $n := (keys .Values.mcpServers | sortAlpha) }}{{ if $i }},{{ end }}{{ $n }}-mcp{{ end }}" }
{{- end -}}
