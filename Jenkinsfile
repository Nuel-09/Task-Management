pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    parameters {
        booleanParam(
            name: 'ENABLE_GITHUB_DEPLOYMENTS',
            defaultValue: true,
            description: 'Send deployment status to GitHub Environments via API'
        )
    }

    environment {
        IMAGE_NAME = 'python-todo-app'
        IMAGE_TAG = 'local'
        COVERAGE_THRESHOLD = '70'
        GITHUB_REPO = 'Nuel-09/Task-Management'
        GITHUB_TOKEN_CREDENTIALS = 'github-api-token'
        DEPLOY_ENV = ''
        DEPLOY_PORT = ''
        COMPOSE_OVERLAY = ''
        DEPLOYMENT_ID_FILE = '.github_deployment_id'
        GITHUB_DEPLOYMENT_ID = ''
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Select Deployment Environment') {
            steps {
                script {
                    def branchName = (env.BRANCH_NAME ?: env.GIT_BRANCH ?: 'main').replaceFirst('^origin/', '')
                    echo "Detected branch: ${branchName}"

                    if (branchName == 'dev') {
                        env.DEPLOY_ENV = 'dev'
                        env.DEPLOY_PORT = '8000'
                        env.COMPOSE_OVERLAY = 'docker-compose.dev.yml'
                    } else if (branchName == 'staging') {
                        env.DEPLOY_ENV = 'staging'
                        env.DEPLOY_PORT = '8001'
                        env.COMPOSE_OVERLAY = 'docker-compose.staging.yml'
                    } else if (branchName == 'main' || branchName == 'master') {
                        env.DEPLOY_ENV = 'prod'
                        env.DEPLOY_PORT = '8002'
                        env.COMPOSE_OVERLAY = 'docker-compose.prod.yml'
                    } else {
                        echo "No deployment target for branch '${branchName}'. Build and tests only."
                    }
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'python -m pip install --upgrade pip'
                        sh 'pip install -r requirements.txt'
                    } else {
                        bat 'python -m pip install --upgrade pip'
                        bat 'pip install -r requirements.txt'
                    }
                }
            }
        }

        stage('Syntax Check') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'python -m compileall app tests scripts'
                    } else {
                        bat 'python -m compileall app tests scripts'
                    }
                }
            }
        }

        stage('Unit Tests + Coverage Gate') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'mkdir -p reports'
                        sh "python -m pytest tests -v --junitxml=reports/junit.xml --cov=app --cov-report=term --cov-report=xml:reports/coverage.xml --cov-fail-under=${env.COVERAGE_THRESHOLD}"
                    } else {
                        bat 'if not exist reports mkdir reports'
                        bat "python -m pytest tests -v --junitxml=reports/junit.xml --cov=app --cov-report=term --cov-report=xml:reports/coverage.xml --cov-fail-under=${env.COVERAGE_THRESHOLD}"
                    }
                }
            }
            post {
                always {
                    junit testResults: 'reports/junit.xml', allowEmptyResults: false
                    archiveArtifacts artifacts: 'reports/*', fingerprint: true
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    env.IMAGE_TAG = (env.GIT_COMMIT ?: 'local').take(7)
                    if (isUnix()) {
                        sh "docker build -t ${env.IMAGE_NAME}:${env.IMAGE_TAG} -t ${env.IMAGE_NAME}:latest ."
                    } else {
                        bat "docker build -t ${env.IMAGE_NAME}:${env.IMAGE_TAG} -t ${env.IMAGE_NAME}:latest ."
                    }
                }
            }
        }

        stage('Create GitHub Deployment') {
            when {
                expression { return env.DEPLOY_ENV?.trim() && params.ENABLE_GITHUB_DEPLOYMENTS }
            }
            steps {
                withCredentials([string(credentialsId: env.GITHUB_TOKEN_CREDENTIALS, variable: 'GITHUB_TOKEN')]) {
                    script {
                        def refSha = env.GIT_COMMIT ?: 'main'
                        def environmentUrl = "http://localhost:${env.DEPLOY_PORT}"
                        def description = "Jenkins deployment ${env.BUILD_TAG}"

                        if (isUnix()) {
                            sh "python scripts/github_deploy.py create --repo ${env.GITHUB_REPO} --token ${env.GITHUB_TOKEN} --ref ${refSha} --environment ${env.DEPLOY_ENV} --environment-url ${environmentUrl} --description \"${description}\" --output-file ${env.DEPLOYMENT_ID_FILE}"
                        } else {
                            bat "python scripts\\github_deploy.py create --repo ${env.GITHUB_REPO} --token %GITHUB_TOKEN% --ref ${refSha} --environment ${env.DEPLOY_ENV} --environment-url ${environmentUrl} --description \"${description}\" --output-file ${env.DEPLOYMENT_ID_FILE}"
                        }

                        env.GITHUB_DEPLOYMENT_ID = readFile(env.DEPLOYMENT_ID_FILE).trim()
                        echo "GitHub deployment id: ${env.GITHUB_DEPLOYMENT_ID}"

                        if (isUnix()) {
                            sh "python scripts/github_deploy.py update --repo ${env.GITHUB_REPO} --token ${env.GITHUB_TOKEN} --deployment-id ${env.GITHUB_DEPLOYMENT_ID} --state in_progress --environment ${env.DEPLOY_ENV} --environment-url ${environmentUrl} --log-url ${env.BUILD_URL}"
                        } else {
                            bat "python scripts\\github_deploy.py update --repo ${env.GITHUB_REPO} --token %GITHUB_TOKEN% --deployment-id ${env.GITHUB_DEPLOYMENT_ID} --state in_progress --environment ${env.DEPLOY_ENV} --environment-url ${environmentUrl} --log-url ${env.BUILD_URL}"
                        }
                    }
                }
            }
        }

        stage('Approval (Staging -> Prod)') {
            when {
                expression { return env.DEPLOY_ENV == 'prod' }
            }
            steps {
                input message: 'Approve production deployment?', ok: 'Deploy prod'
            }
        }

        stage('Deploy Docker Environment') {
            when {
                expression { return env.DEPLOY_ENV?.trim() }
            }
            steps {
                script {
                    def composeCommand = "docker compose -f docker-compose.yml -f ${env.COMPOSE_OVERLAY} --project-name todo-${env.DEPLOY_ENV} up -d --build"
                    def psCommand = "docker compose -f docker-compose.yml -f ${env.COMPOSE_OVERLAY} --project-name todo-${env.DEPLOY_ENV} ps"

                    if (isUnix()) {
                        sh composeCommand
                        sh psCommand
                    } else {
                        bat composeCommand
                        bat psCommand
                    }
                }
            }
        }

        stage('Smoke Test Deployment') {
            when {
                expression { return env.DEPLOY_ENV?.trim() }
            }
            steps {
                script {
                    def smokeCommand = "python -c \"import urllib.request; p='${env.DEPLOY_PORT}'; h=urllib.request.urlopen(f'http://localhost:{p}/health'); assert h.status==200; r=urllib.request.urlopen(f'http://localhost:{p}/'); assert r.status==200; print('smoke ok for', p)\""
                    if (isUnix()) {
                        sh smokeCommand
                    } else {
                        bat smokeCommand
                    }
                }
            }
        }

        stage('Mark GitHub Deployment Success') {
            when {
                expression { return env.GITHUB_DEPLOYMENT_ID?.trim() && params.ENABLE_GITHUB_DEPLOYMENTS }
            }
            steps {
                withCredentials([string(credentialsId: env.GITHUB_TOKEN_CREDENTIALS, variable: 'GITHUB_TOKEN')]) {
                    script {
                        def environmentUrl = "http://localhost:${env.DEPLOY_PORT}"
                        if (isUnix()) {
                            sh "python scripts/github_deploy.py update --repo ${env.GITHUB_REPO} --token ${env.GITHUB_TOKEN} --deployment-id ${env.GITHUB_DEPLOYMENT_ID} --state success --environment ${env.DEPLOY_ENV} --environment-url ${environmentUrl} --log-url ${env.BUILD_URL}"
                        } else {
                            bat "python scripts\\github_deploy.py update --repo ${env.GITHUB_REPO} --token %GITHUB_TOKEN% --deployment-id ${env.GITHUB_DEPLOYMENT_ID} --state success --environment ${env.DEPLOY_ENV} --environment-url ${environmentUrl} --log-url ${env.BUILD_URL}"
                        }
                    }
                }
            }
        }
    }

    post {
        failure {
            script {
                if (env.GITHUB_DEPLOYMENT_ID?.trim() && params.ENABLE_GITHUB_DEPLOYMENTS) {
                    withCredentials([string(credentialsId: env.GITHUB_TOKEN_CREDENTIALS, variable: 'GITHUB_TOKEN')]) {
                        def environmentUrl = env.DEPLOY_PORT?.trim() ? "http://localhost:${env.DEPLOY_PORT}" : "http://localhost"
                        if (isUnix()) {
                            sh "python scripts/github_deploy.py update --repo ${env.GITHUB_REPO} --token ${env.GITHUB_TOKEN} --deployment-id ${env.GITHUB_DEPLOYMENT_ID} --state failure --environment ${env.DEPLOY_ENV} --environment-url ${environmentUrl} --log-url ${env.BUILD_URL}"
                        } else {
                            bat "python scripts\\github_deploy.py update --repo ${env.GITHUB_REPO} --token %GITHUB_TOKEN% --deployment-id ${env.GITHUB_DEPLOYMENT_ID} --state failure --environment ${env.DEPLOY_ENV} --environment-url ${environmentUrl} --log-url ${env.BUILD_URL}"
                        }
                    }
                }
            }
        }
        always {
            script {
                if (fileExists(env.DEPLOYMENT_ID_FILE)) {
                    if (isUnix()) {
                        sh "rm -f ${env.DEPLOYMENT_ID_FILE}"
                    } else {
                        bat "del /f /q ${env.DEPLOYMENT_ID_FILE}"
                    }
                }
            }
        }
    }
}