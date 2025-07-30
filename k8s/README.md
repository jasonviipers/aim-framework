# Kubernetes Deployment Configuration for AIM Framework

This directory contains Kubernetes manifests for deploying the AIM Framework in a Kubernetes cluster.

## Files

- `namespace.yaml` - Creates the aim-framework namespace
- `configmap.yaml` - Configuration files and settings
- `secret.yaml` - Sensitive configuration data
- `deployment.yaml` - Main application deployment
- `service.yaml` - Service definitions
- `ingress.yaml` - Ingress configuration for external access
- `hpa.yaml` - Horizontal Pod Autoscaler
- `pvc.yaml` - Persistent Volume Claims for data storage

## Quick Deployment

```bash
# Apply all configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n aim-framework

# View logs
kubectl logs -f deployment/aim-framework -n aim-framework
```

## Customization

1. Update `configmap.yaml` with your configuration
2. Set secrets in `secret.yaml`
3. Modify resource limits in `deployment.yaml`
4. Configure ingress domain in `ingress.yaml`

## Scaling

```bash
# Manual scaling
kubectl scale deployment aim-framework --replicas=5 -n aim-framework

# Auto-scaling is configured via hpa.yaml
```