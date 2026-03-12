pipeline {
    agent any

    environment {
        DEPLOY_DIR = '/home/venomaru/deploy/money-manager'
    }

    stages {
        stage('Deploy') {
            steps {
                sh '''
                    # Copy source files to deploy directory (build context)
                    cp main.py models.py store.py requirements.txt Dockerfile .dockerignore "$DEPLOY_DIR/"
                    cp -r static/* "$DEPLOY_DIR/static/"

                    # Rebuild and restart container
                    cd "$DEPLOY_DIR"
                    docker compose up -d --build --force-recreate
                '''
            }
        }
    }

    post {
        success { echo 'Money Manager deployed successfully' }
        failure { echo 'Money Manager deployment failed' }
    }
}
