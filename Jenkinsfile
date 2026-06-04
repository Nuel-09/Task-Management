def currentBranchName() {
    return (env.BRANCH_NAME ?: env.GIT_BRANCH ?: 'main').replaceFirst('^origin/', '')
}

def resolveDeployConfig(String branchName) {
    if (branchName == 'dev') {
        return [envName: 'dev', port: '8000', overlay: 'docker-compose.dev.yml']
    }
    if (branchName == 'staging') {
        return [envName: 'staging', port: '8001', overlay: 'docker-compose.staging.yml']
    }
    if (branchName == 'main' || branchName == 'master') {
        return [envName: 'prod', port: '8002', overlay: 'docker-compose.prod.yml']
    }
    return null
}

def shouldDeploy(String branchName) {
    return resolveDeployConfig(branchName) != null
}

def applyDeployConfig(Map deployConfig) {
    env.DEPLOY_ENV = deployConfig.envName
    env.DEPLOY_PORT = deployConfig.port
    env.COMPOSE_OVERLAY = deployConfig.overlay
}

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
                    def branchName = currentBranchName()
                    def deployConfig = resolveDeployConfig(branchName)
                    echo "Detected branch: ${branchName}"

                    if (deployConfig) {
                        applyDeployConfig(deployConfig)
                        echo "Deployment target: ${env.DEPLOY_ENV} on port ${env.DEPLOY_PORT}"
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
                expression {
                    return shouldDeploy(currentBranchName()) && params.ENABLE_GITHUB_DEPLOYMENTS
                }
            }
            steps {
                script {
                    applyDeployConfig(resolveDeployConfig(currentBranchName()))
                }
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
                expression {
                    def deployConfig = resolveDeployConfig(currentBranchName())
                    return deployConfig != null && deployConfig.envName == 'prod'
                }
            }
            steps {
                input message: 'Approve production deployment?', ok: 'Deploy prod'
            }
        }

        stage('Deploy Docker Environment') {
            when {
                expression { return shouldDeploy(currentBranchName()) }
            }
            steps {
                script {
                    applyDeployConfig(resolveDeployConfig(currentBranchName()))
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
                expression { return shouldDeploy(currentBranchName()) }
            }
            steps {
                script {
                    applyDeployConfig(resolveDeployConfig(currentBranchName()))
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
                expression {
                    return shouldDeploy(currentBranchName()) && params.ENABLE_GITHUB_DEPLOYMENTS
                }
            }
            steps {
                script {
                    applyDeployConfig(resolveDeployConfig(currentBranchName()))
                    if (!env.GITHUB_DEPLOYMENT_ID?.trim() && fileExists(env.DEPLOYMENT_ID_FILE)) {
                        env.GITHUB_DEPLOYMENT_ID = readFile(env.DEPLOYMENT_ID_FILE).trim()
                    }
                }
                withCredentials([string(credentialsId: env.GITHUB_TOKEN_CREDENTIALS, variable: 'GITHUB_TOKEN')]) {
                    script {
                        def deploymentId = env.GITHUB_DEPLOYMENT_ID?.trim()
                        if (!deploymentId) {
                            error 'Missing GitHub deployment id; Create GitHub Deployment stage may have failed.'
                        }
                        def environmentUrl = "http://localhost:${env.DEPLOY_PORT}"
                        if (isUnix()) {
                            sh "python scripts/github_deploy.py update --repo ${env.GITHUB_REPO} --token ${env.GITHUB_TOKEN} --deployment-id ${deploymentId} --state success --environment ${env.DEPLOY_ENV} --environment-url ${environmentUrl} --log-url ${env.BUILD_URL}"
                        } else {
                            bat "python scripts\\github_deploy.py update --repo ${env.GITHUB_REPO} --token %GITHUB_TOKEN% --deployment-id ${deploymentId} --state success --environment ${env.DEPLOY_ENV} --environment-url ${environmentUrl} --log-url ${env.BUILD_URL}"
                        }
                    }
                }
            }
        }
    }

    post {
        failure {
            script {
                def deployConfig = resolveDeployConfig(currentBranchName())
                if (env.GITHUB_DEPLOYMENT_ID?.trim() && params.ENABLE_GITHUB_DEPLOYMENTS && deployConfig) {
                    applyDeployConfig(deployConfig)
                    withCredentials([string(credentialsId: env.GITHUB_TOKEN_CREDENTIALS, variable: 'GITHUB_TOKEN')]) {
                        def environmentUrl = "http://localhost:${env.DEPLOY_PORT}"
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
