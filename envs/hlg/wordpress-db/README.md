# wordpress-db (hlg)

Este diretório descreve um MariaDB gerenciado pelo Argo CD para servir o WordPress.

## Fluxo
1. Faça commit/merge das mudanças.
2. O ApplicationSet `apps-by-env` já observa `envs/*/*/overlay`, então o Argo CD criará um Application chamado `wordpress-db-hlg` automaticamente.
3. Após sincronizar, o banco ficará disponível via serviço `wordpress-db-mariadb` no namespace `wordpress-db`.

## Endpoints importantes
- Serviço interno: `wordpress-db-mariadb.wordpress-db.svc.cluster.local:3306`
- Usuário: `wordpress`
- Database: `wordpress`
- Senha: ver Secret `wordpress-db-mariadb` (o valor padrão neste repo é `wordpresspass`, troque em produção).

## Dependências
- StorageClass padrão precisa suportar `ReadWriteOnce` e volumes de pelo menos `5Gi`.
- Para kind, isso funciona com o provisionador local padrão.

## Próximos passos
- Altere `auth.*` em `base/kustomization.yaml` para usar senhas seguras ou integre com Sealed Secrets.
- Configure o Deployment do WordPress com as variáveis:
  - `WORDPRESS_DB_HOST=wordpress-db-mariadb.wordpress-db.svc.cluster.local`
  - `WORDPRESS_DB_USER=wordpress`
  - `WORDPRESS_DB_PASSWORD=<seguir o Secret>`
  - `WORDPRESS_DB_NAME=wordpress`
