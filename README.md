# GitOps (Argo CD + ApplicationSet + Kustomize)

Este repositório implementa o fluxo:

1. **Bootstrap do cluster** (instala Argo CD)
2. **App of Apps** (por cluster) aplica:
   - AppProjects (core x negócio)
   - RBAC/Policies do Argo CD
   - Um "app" que aplica os ApplicationSets
3. **ApplicationSet** descobre apps automaticamente em `envs/<env>/<app>/overlay`
4. **Apps** usam Kustomize no padrão `base` + `overlay`.

## Estrutura

- `clusters/<cluster>/apps`: raiz (App of Apps) + projects + apps auxiliares
- `applicationsets`: definição dos ApplicationSets (separado por ambiente em `applicationsets/hlg` e `applicationsets/prd`)
- `envs/<env>/<app>/{base,overlay}`: Kustomize por app
- `policies`: configs do Argo CD (ignoreDifferences etc.)
- `rbac`: RBAC do Argo CD + notas de boundaries

## Bootstrap (migração segura)

Para cenário **100% local com KIND**, siga o guia: `docs/kind-local-argocd.md`.

### 1) Instalar Argo CD (por cluster)

```bash
kubectl create ns argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### 2) Ajustar `repoURL`

Substitua `https://github.com/sua-org/gitops.git` pelos seus valores reais nos manifests em:

- `clusters/**/apps/*.yaml`
- `applicationsets/*.yaml`

### 3) Aplicar o App of Apps (por cluster)

Homologação:

```bash
kubectl apply -n argocd -f clusters/aks-hlg/apps/app-of-apps.yaml
```

Produção:

```bash
kubectl apply -n argocd -f clusters/aks-prd/apps/app-of-apps.yaml
```

### 4) Validar (piloto)

Escolha um app de baixa criticidade (ex.: `cloudflared`), compare o drift, ajuste manifests/patches e só então habilite sync automático em homologação.

### 5) Produção começa manual

Por padrão, o App of Apps de produção está **sem** sync automático. Depois de estabilizar, ligue `automated.prune/selfHeal` gradualmente.

## Observações

- Os diretórios de apps em `envs/` estão com **skeleton** de Kustomize (não cria recursos reais ainda).
- `applicationsets/hlg/apps-by-env.yaml` considera `envs/hlg/*/overlay` (automático).
- `applicationsets/prd/apps-by-env.yaml` considera `envs/prd/*/overlay` (manual).
- `applicationsets/apps-matrix.yaml` é um exemplo de multi-cluster (exige clusters registrados no Argo CD).
