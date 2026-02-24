# Argo CD com KIND (tudo local) — passo a passo

## Por que o `repoURL` não pode ser “local”

O Argo CD roda **dentro do cluster** (pods como `argocd-repo-server`).
Então, quando você coloca `repoURL: ...`, quem precisa acessar esse Git é o **pod**, não o seu terminal.

Isso significa:

- Não existe `repoURL` do tipo “caminho local” (ex.: `/home/junior/gitops`) que funcione.
- Você precisa de um Git acessível por rede a partir do cluster.

Para um ambiente 100% local com KIND, a forma mais simples e previsível é subir um **Git server dentro do próprio cluster**.

## Opção recomendada: Gitea dentro do KIND

### 0) Pré-requisitos

- `kind`, `kubectl`, `helm`, `git`

### 1) Criar o cluster KIND (se ainda não existir)

Exemplo simples:

```bash
kind create cluster --name gitops
```

### 2) Instalar o Gitea no cluster

```bash
helm repo add gitea-charts https://dl.gitea.com/charts/
helm repo update
kubectl create ns gitea
helm install gitea gitea-charts/gitea -n gitea
```

Depois, abra a UI via port-forward:

```bash
kubectl -n gitea port-forward svc/gitea-http 3000:3000
```

Acesse `http://localhost:3000`, crie um usuário e crie um repo chamado `gitops`.

### 3) Subir este repositório para o Gitea

No seu workspace local (este repo):

```bash
git init
git add .
git commit -m "bootstrap gitops"

git remote add origin http://localhost:3000/<SEU_USUARIO>/gitops.git
git push -u origin main
```

### 4) Definir o `repoURL` correto nos manifests

Como o Argo CD está no cluster, o `repoURL` deve ser o **endereço interno** do Service do Gitea:

```yaml
repoURL: http://gitea-http.gitea.svc.cluster.local:3000/<SEU_USUARIO>/gitops.git
```

Substitua `https://github.com/sua-org/gitops.git` por esse valor nos arquivos:

- `clusters/**/apps/*.yaml`
- `applicationsets/**/apps-by-env.yaml`

### 5) Instalar Argo CD

```bash
kubectl create ns argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

Abra a UI:

```bash
kubectl -n argocd port-forward svc/argocd-server 8080:443
```

### 6) Conectar o Argo CD ao repositório (Gitea)

Se o seu Gitea exigir autenticação, crie um token no Gitea e adicione o repositório no Argo CD (UI: Settings → Repositories).

Se você quiser via CLI, instale `argocd` e use algo como:

```bash
argocd repo add http://gitea-http.gitea.svc.cluster.local:3000/<SEU_USUARIO>/gitops.git \
  --username <SEU_USUARIO> \
  --password <TOKEN_OU_SENHA>
```

### 7) Aplicar o App of Apps

Homologação:

```bash
kubectl apply -n argocd -f clusters/aks-hlg/apps/app-of-apps.yaml
```

Produção (manual por padrão):

```bash
kubectl apply -n argocd -f clusters/aks-prd/apps/app-of-apps.yaml
```

### 8) O que vai acontecer na prática

- O root app aplica `clusters/<cluster>/apps/kustomization.yaml`
- Isso cria os `AppProject` (core/negócio)
- Aplica policies (ignore diffs) e RBAC
- Aplica o ApplicationSet do ambiente (`applicationsets/hlg` ou `applicationsets/prd`)
- O ApplicationSet cria 1 Application por diretório `envs/<env>/<app>/overlay`

## Como lidar com build/imagens no KIND

O Argo CD **não faz build** por conta própria; ele sincroniza manifests.

No fluxo local com KIND, o mais comum é:

1) Build da imagem no seu Docker local
```bash
docker build -t firefly:dev .
```

2) Carregar no cluster KIND
```bash
kind load docker-image firefly:dev --name gitops
```

3) No seu Deployment, use `image: firefly:dev` e `imagePullPolicy: IfNotPresent`

4) Commit/push da mudança de manifest no Git → Argo CD sincroniza

## Migração segura (sem quebrar produção)

1) Comece com 1 app piloto (ex.: `cloudflared`)
2) Compare e ajuste drifts
3) Só depois habilite `automated` em HLG
4) Em PRD, mantenha manual até estabilizar
