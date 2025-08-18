#!/bin/bash
set -e

# Secrets
VPS_USER="${USER_SERVEUR:?}"
VPS_HOST="${IP_SERVEUR:?}"
VPS_SSH_KEY="${SSH_SERVEUR:?}"
DOCKER_USERNAME="${DOCKERHUB_USERNAME:?}"
DOCKER_TOKEN="${DOCKERHUB_TOKEN:?}"
IMAGE_NAME="backend-pci-app"

# Créer un fichier temporaire contenant la clé SSH
TMP_KEY_FILE=$(mktemp)
echo "$VPS_SSH_KEY" > "$TMP_KEY_FILE"
chmod 600 "$TMP_KEY_FILE"

REMOTE_FILE_TO_EXECUTE="pull_docker_img_"$IMAGE_NAME".sh"
REMOTE_FILE_PATH="/home/$VPS_USER/pull_docker_img_$IMAGE_NAME.sh"
REMOTE_ENV_SCRIPT="/home/$VPS_USER/creation_env_prod.sh"
REMOTE_ENV_PROD_FILE="/home/$VPS_USER/.env.prod"

# Fonction de nettoyage local
cleanup_local() {
    echo "🧹 Nettoyage local..."
    rm -f "$TMP_KEY_FILE"
    echo "✅ Nettoyage local terminé."
}

# Fonction de nettoyage distant
cleanup_remote() {
    echo "🧹 Nettoyage des fichiers sur le serveur distant..."
    ssh -i "$TMP_KEY_FILE" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$VPS_USER@$VPS_HOST" "
        echo '🗑️ Suppression des fichiers temporaires...'
        sudo rm -f '$REMOTE_FILE_PATH' || rm -f '$REMOTE_FILE_PATH'
        sudo rm -f '$REMOTE_ENV_SCRIPT' || rm -f '$REMOTE_ENV_SCRIPT'
        echo '🗑️ Suppression obligatoire du fichier .env.prod...'
        sudo rm -f '$REMOTE_ENV_PROD_FILE' || rm -f '$REMOTE_ENV_PROD_FILE'
        echo '✅ Fichiers temporaires et .env.prod supprimés du serveur distant.'
    " 2>/dev/null || echo "⚠️ Certains fichiers n'ont pas pu être supprimés (peut-être inexistants)"
}

# Piége pour nettoyer en cas d'interruption
trap 'cleanup_remote; cleanup_local; echo "❌ Script interrompu - nettoyage effectué"; exit 1' INT TERM ERR

echo "⏳ Test de connexion SSH..."
timeout 10s ssh -i "$TMP_KEY_FILE" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$VPS_USER@$VPS_HOST" "echo '✅ Connexion SSH OK'"

echo "🔍 Vérification de l'existence du fichier distant..."

ssh -i "$TMP_KEY_FILE" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$VPS_USER@$VPS_HOST" "
  if [ -f '$REMOTE_FILE_PATH' ]; then
    echo '⚠️ Le fichier $REMOTE_FILE_PATH existe déjà et sera remplacé.'
    sudo rm -f '$REMOTE_FILE_PATH' || rm -f '$REMOTE_FILE_PATH'
  else
    echo '✅ Aucun fichier $REMOTE_FILE_PATH détecté. Prêt à copier.'
  fi
  
  if [ -f '$REMOTE_ENV_SCRIPT' ]; then
    echo '⚠️ Le fichier $REMOTE_ENV_SCRIPT existe déjà et sera remplacé.'
    sudo rm -f '$REMOTE_ENV_SCRIPT' || rm -f '$REMOTE_ENV_SCRIPT'
  fi

  if [ -f '$REMOTE_ENV_PROD_FILE' ]; then
    echo '⚠️ Le fichier .env.prod existe et sera supprimé.'
    sudo rm -f '$REMOTE_ENV_PROD_FILE' || rm -f '$REMOTE_ENV_PROD_FILE'
  fi
"

echo "📤 Copie du script de création d'environnement vers le serveur distant..."

scp -i "$TMP_KEY_FILE" \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null \
  ./scripts/creation_env_prod.sh \
  "$VPS_USER@$VPS_HOST:$REMOTE_ENV_SCRIPT"

echo "📤 Copie du script vers le serveur distant..."

scp -i "$TMP_KEY_FILE" \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null \
  ./scripts/pull_docker_img.sh \
  "$VPS_USER@$VPS_HOST:$REMOTE_FILE_PATH"





echo "🔐 Exécution du script distant..."

ssh -i "$TMP_KEY_FILE" -o StrictHostKeyChecking=no "$VPS_USER@$VPS_HOST" <<EOF
  export DOCKERHUB_USERNAME="$DOCKER_USERNAME"
  export DOCKERHUB_TOKEN="$DOCKER_TOKEN"

  # === Secrets de configuration pour .env.prod ===
  export DB_HOST="${DB_HOST}"
  export DB_PORT="${DB_PORT}"
  export DB_USER="${DB_USER}"
  export DB_PASSWORD="${DB_PASSWORD}"
  export DB_NAME="${DB_NAME}"

  export MONGO_URL="${MONGO_URL}"
  export MONGO_DB_NAME="${MONGO_DB_NAME}"

  export EMAIL_HOST="${EMAIL_HOST}"
  export EMAIL_USER="${EMAIL_USER}"
  export EMAIL_PASS="${EMAIL_PASS}"

  export JWT_SECRET="${JWT_SECRET}"
  export FRONTEND_URL="${FRONTEND_URL}"

  
  # === Génération du fichier .env.prod et exécution de l'app ===
  cd /home/$VPS_USER

  chmod +x creation_env_prod.sh
  ./creation_env_prod.sh

  chmod +x $REMOTE_FILE_TO_EXECUTE
  ./$REMOTE_FILE_TO_EXECUTE

  # === Nettoyage automatique des scripts temporaires ===
  echo "🧹 Nettoyage des scripts temporaires sur le serveur..."
  sudo rm -f '$REMOTE_FILE_PATH' || rm -f '$REMOTE_FILE_PATH'
  sudo rm -f '$REMOTE_ENV_SCRIPT' || rm -f '$REMOTE_ENV_SCRIPT'
  echo "✅ Scripts temporaires supprimés."
EOF



# Nettoyage final
cleanup_local

echo "✅ Déploiement terminé avec nettoyage automatique."



































# #!/bin/bash
# set -e

# # Secrets
# VPS_USER="${USER_SERVEUR:?}"
# VPS_HOST="${IP_SERVEUR:?}"
# VPS_SSH_KEY="${SSH_SERVEUR:?}"
# DOCKER_USERNAME="${DOCKERHUB_USERNAME:?}"
# DOCKER_TOKEN="${DOCKERHUB_TOKEN:?}"
# IMAGE_NAME="backend-pci-app"

# # Créer un fichier temporaire contenant la clé SSH
# TMP_KEY_FILE=$(mktemp)
# echo "$VPS_SSH_KEY" > "$TMP_KEY_FILE"
# chmod 600 "$TMP_KEY_FILE"

# REMOTE_FILE_TO_EXECUTE="pull_docker_img_"$IMAGE_NAME".sh"
# REMOTE_FILE_PATH="/home/$VPS_USER/pull_docker_img_$IMAGE_NAME.sh"
# REMOTE_ENV_SCRIPT="/home/$VPS_USER/creation_env_prod.sh"

# # Fonction de nettoyage local
# cleanup_local() {
#     echo "🧹 Nettoyage local..."
#     rm -f "$TMP_KEY_FILE"
#     echo "✅ Nettoyage local terminé."
# }

# # Fonction de nettoyage distant
# cleanup_remote() {
#     echo "🧹 Nettoyage des fichiers sur le serveur distant..."
#     ssh -i "$TMP_KEY_FILE" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$VPS_USER@$VPS_HOST" "
#         echo '🗑️ Suppression des fichiers temporaires...'
#         sudo rm -f '$REMOTE_FILE_PATH' || rm -f '$REMOTE_FILE_PATH'
#         sudo rm -f '$REMOTE_ENV_SCRIPT' || rm -f '$REMOTE_ENV_SCRIPT'
#         echo '✅ Fichiers temporaires supprimés du serveur distant.'
#     " 2>/dev/null || echo "⚠️ Certains fichiers n'ont pas pu être supprimés (peut-être inexistants)"
# }

# # Piége pour nettoyer en cas d'interruption
# trap 'cleanup_remote; cleanup_local; echo "❌ Script interrompu - nettoyage effectué"; exit 1' INT TERM ERR

# echo "⏳ Test de connexion SSH..."
# timeout 10s ssh -i "$TMP_KEY_FILE" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$VPS_USER@$VPS_HOST" "echo '✅ Connexion SSH OK'"

# echo "🔍 Vérification de l'existence du fichier distant..."

# ssh -i "$TMP_KEY_FILE" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$VPS_USER@$VPS_HOST" "
#   if [ -f '$REMOTE_FILE_PATH' ]; then
#     echo '⚠️ Le fichier $REMOTE_FILE_PATH existe déjà et sera remplacé.'
#     sudo rm -f '$REMOTE_FILE_PATH' || rm -f '$REMOTE_FILE_PATH'
#   else
#     echo '✅ Aucun fichier $REMOTE_FILE_PATH détecté. Prêt à copier.'
#   fi
  
#   if [ -f '$REMOTE_ENV_SCRIPT' ]; then
#     echo '⚠️ Le fichier $REMOTE_ENV_SCRIPT existe déjà et sera remplacé.'
#     sudo rm -f '$REMOTE_ENV_SCRIPT' || rm -f '$REMOTE_ENV_SCRIPT'
#   fi
# "

# echo "📤 Copie du script de création d'environnement vers le serveur distant..."

# scp -i "$TMP_KEY_FILE" \
#   -o StrictHostKeyChecking=no \
#   -o UserKnownHostsFile=/dev/null \
#   ./scripts/creation_env_prod.sh \
#   "$VPS_USER@$VPS_HOST:$REMOTE_ENV_SCRIPT"

# echo "📤 Copie du script vers le serveur distant..."

# scp -i "$TMP_KEY_FILE" \
#   -o StrictHostKeyChecking=no \
#   -o UserKnownHostsFile=/dev/null \
#   ./scripts/pull_docker_img.sh \
#   "$VPS_USER@$VPS_HOST:$REMOTE_FILE_PATH"





# echo "🔐 Exécution du script distant..."

# ssh -i "$TMP_KEY_FILE" -o StrictHostKeyChecking=no "$VPS_USER@$VPS_HOST" <<EOF
#   export DOCKERHUB_USERNAME="$DOCKER_USERNAME"
#   export DOCKERHUB_TOKEN="$DOCKER_TOKEN"

#   # === Secrets de configuration pour .env.prod ===
#   export DB_HOST="${DB_HOST}"
#   export DB_PORT="${DB_PORT}"
#   export DB_USER="${DB_USER}"
#   export DB_PASSWORD="${DB_PASSWORD}"
#   export DB_NAME="${DB_NAME}"

#   export MONGO_URL="${MONGO_URL}"
#   export MONGO_DB_NAME="${MONGO_DB_NAME}"

#   export EMAIL_HOST="${EMAIL_HOST}"
#   export EMAIL_USER="${EMAIL_USER}"
#   export EMAIL_PASS="${EMAIL_PASS}"

#   export JWT_SECRET="${JWT_SECRET}"
#   export FRONTEND_URL="${FRONTEND_URL}"

  
#   # === Génération du fichier .env.prod et exécution de l'app ===
#   cd /home/$VPS_USER

#   chmod +x creation_env_prod.sh
#   ./creation_env_prod.sh

#   chmod +x $REMOTE_FILE_TO_EXECUTE
#   ./$REMOTE_FILE_TO_EXECUTE

#   # === Nettoyage automatique des scripts temporaires ===
#   echo "🧹 Nettoyage des scripts temporaires sur le serveur..."
#   sudo rm -f '$REMOTE_FILE_PATH' || rm -f '$REMOTE_FILE_PATH'
#   sudo rm -f '$REMOTE_ENV_SCRIPT' || rm -f '$REMOTE_ENV_SCRIPT'
#   echo "✅ Scripts temporaires supprimés."
# EOF

# # Nettoyage final
# cleanup_local









# echo "✅ Déploiement terminé avec nettoyage automatique."

