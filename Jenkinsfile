// Deploy settings are NEVER stored in env.* — Declarative environment{} values
// cannot be reliably updated from script blocks on Windows agents.
// Always call deployConfigForCurrentBranch() where deploy settings are needed.

def currentBranchName() {
    return (env.BRANCH_NAME ?: env.GIT_BRANCH ?: 'main').replaceFirst('^origin/', '')
}

def resolveDeployConfig(String branchName) {
    if (branchName == 'dev') {
        return [target: 'dev', port: '8000', overlay: 'docker-compose.dev.yml']
    }
    if (branchName == 'staging') {
        return [target: 'staging', port: '8001', overlay: 'docker-compose.staging.yml']
    }
    if (branchName == 'main' || branchName == 'master') {
        return [target: 'prod', port: '8002', overlay: 'docker-compose.prod.yml']
    }
    return null
}

def deployConfigForCurrentBranch() {
    return resolveDeployConfig(currentBranchName())
}

def shouldDeployCurrentBranch() {
    return deployConfigForCurrentBranch() != null
}

def readGithubDeploymentId() {
    def idFile = '.github_deployment_id'
    if (fileExists(idFile)) {
        return readFile(idFile).trim()
    }
    return ''
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
        // Secret file credential: upload your local .env once in Jenkins (see README).
        ENV_FILE_CREDENTIALS = 'todo-app-dotenv'
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
                    def cfg = resolveDeployConfig(branchName)
                    echo "Detected branch: ${branchName}"
                    if (cfg) {
                        echo "Deployment target: ${cfg['target']} on port ${cfg['port']} (${cfg['overlay']})"
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
                    return shouldDeployCurrentBranch() && params.ENABLE_GITHUB_DEPLOYMENTS
                }
            }
            steps {
                withCredentials([string(credentialsId: env.GITHUB_TOKEN_CREDENTIALS, variable: 'GITHUB_TOKEN')]) {
                    script {
                        def cfg = deployConfigForCurrentBranch()
                        def refSha = env.GIT_COMMIT ?: 'main'
                        def environmentUrl = "http://localhost:${cfg['port']}"
                        def description = "Jenkins deployment ${env.BUILD_TAG}"
                        def target = cfg['target']

                        if (isUnix()) {
                            sh "python scripts/github_deploy.py create --repo ${env.GITHUB_REPO} --token ${env.GITHUB_TOKEN} --ref ${refSha} --environment ${target} --environment-url ${environmentUrl} --description \"${description}\" --output-file .github_deployment_id"
                        } else {
                            bat "python scripts\\github_deploy.py create --repo ${env.GITHUB_REPO} --token %GITHUB_TOKEN% --ref ${refSha} --environment ${target} --environment-url ${environmentUrl} --description \"${description}\" --output-file .github_deployment_id"
                        }

                        def deploymentId = readGithubDeploymentId()
                        echo "GitHub deployment id: ${deploymentId}"
                        if (!deploymentId) {
                            error 'GitHub deployment id file is empty after create.'
                        }

                        if (isUnix()) {
                            sh "python scripts/github_deploy.py update --repo ${env.GITHUB_REPO} --token ${env.GITHUB_TOKEN} --deployment-id ${deploymentId} --state in_progress --environment ${target} --environment-url ${environmentUrl} --log-url ${env.BUILD_URL}"
                        } else {
                            bat "python scripts\\github_deploy.py update --repo ${env.GITHUB_REPO} --token %GITHUB_TOKEN% --deployment-id ${deploymentId} --state in_progress --environment ${target} --environment-url ${environmentUrl} --log-url ${env.BUILD_URL}"
                        }
                    }
                }
            }
        }

        stage('Approval (Staging -> Prod)') {
            when {
                expression {
                    def cfg = deployConfigForCurrentBranch()
                    return cfg != null && cfg['target'] == 'prod'
                }
            }
            steps {
                input message: 'Approve production deployment?', ok: 'Deploy prod'
            }
        }

        stage('Prepare .env from Credentials') {
            when {
                expression { return shouldDeployCurrentBranch() }
            }
            steps {
                withCredentials([file(credentialsId: env.ENV_FILE_CREDENTIALS, variable: 'TODO_DOTENV_FILE')]) {
                    script {
                        if (isUnix()) {
                            sh 'cp "$TODO_DOTENV_FILE" .env && chmod 600 .env'
                        } else {
                            bat "copy /Y \"%TODO_DOTENV_FILE%\" .env"
                        }
                        if (!fileExists('.env')) {
                            error "Could not create .env from Jenkins credential '${env.ENV_FILE_CREDENTIALS}'."
                        }
                        echo '.env prepared from Jenkins secret file (values are not printed in logs).'
                    }
                }
            }
        }

        stage('Deploy Docker Environment') {
            when {
                expression { return shouldDeployCurrentBranch() }
            }
            steps {
                script {
                    def cfg = deployConfigForCurrentBranch()
                    def target = cfg['target']
                    def overlay = cfg['overlay']
                    def compose = "docker compose -f docker-compose.yml -f ${overlay} --project-name todo-${target}"
                    // Fixed container_name in compose files; remove stale container before redeploy.
                    def containerName = "python-todo-app-${target}"
                    def downCommand = "${compose} down --remove-orphans"
                    def upCommand = "${compose} up -d --build --force-recreate --remove-orphans"
                    def psCommand = "${compose} ps"

                    if (isUnix()) {
                        sh "docker rm -f ${containerName} >/dev/null 2>&1 || true"
                        sh downCommand
                        sh upCommand
                        sh psCommand
                    } else {
                        bat "docker rm -f ${containerName} 2>nul || ver >nul"
                        bat downCommand
                        bat upCommand
                        bat psCommand
                    }
                }
            }
        }

        stage('Smoke Test Deployment') {
            when {
                expression { return shouldDeployCurrentBranch() }
            }
            steps {
                script {
                    def port = deployConfigForCurrentBranch()['port']
                    def smokeCommand = "python -c \"import urllib.request; p='${port}'; h=urllib.request.urlopen(f'http://localhost:{p}/health'); assert h.status==200; r=urllib.request.urlopen(f'http://localhost:{p}/'); assert r.status==200; print('smoke ok for', p)\""
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
                    return shouldDeployCurrentBranch() && params.ENABLE_GITHUB_DEPLOYMENTS
                }
            }
            steps {
                withCredentials([string(credentialsId: env.GITHUB_TOKEN_CREDENTIALS, variable: 'GITHUB_TOKEN')]) {
                    script {
                        def cfg = deployConfigForCurrentBranch()
                        def deploymentId = readGithubDeploymentId()
                        if (!deploymentId) {
                            error 'Missing GitHub deployment id; Create GitHub Deployment stage may have failed.'
                        }
                        def environmentUrl = "http://localhost:${cfg['port']}"
                        def target = cfg['target']
                        if (isUnix()) {
                            sh "python scripts/github_deploy.py update --repo ${env.GITHUB_REPO} --token ${env.GITHUB_TOKEN} --deployment-id ${deploymentId} --state success --environment ${target} --environment-url ${environmentUrl} --log-url ${env.BUILD_URL}"
                        } else {
                            bat "python scripts\\github_deploy.py update --repo ${env.GITHUB_REPO} --token %GITHUB_TOKEN% --deployment-id ${deploymentId} --state success --environment ${target} --environment-url ${environmentUrl} --log-url ${env.BUILD_URL}"
                        }
                    }
                }
            }
        }
    }

    post {
        failure {
            script {
                def cfg = deployConfigForCurrentBranch()
                def deploymentId = readGithubDeploymentId()
                if (deploymentId && params.ENABLE_GITHUB_DEPLOYMENTS && cfg) {
                    withCredentials([string(credentialsId: env.GITHUB_TOKEN_CREDENTIALS, variable: 'GITHUB_TOKEN')]) {
                        def environmentUrl = "http://localhost:${cfg['port']}"
                        def target = cfg['target']
                        if (isUnix()) {
                            sh "python scripts/github_deploy.py update --repo ${env.GITHUB_REPO} --token ${env.GITHUB_TOKEN} --deployment-id ${deploymentId} --state failure --environment ${target} --environment-url ${environmentUrl} --log-url ${env.BUILD_URL}"
                        } else {
                            bat "python scripts\\github_deploy.py update --repo ${env.GITHUB_REPO} --token %GITHUB_TOKEN% --deployment-id ${deploymentId} --state failure --environment ${target} --environment-url ${environmentUrl} --log-url ${env.BUILD_URL}"
                        }
                    }
                }
            }
        }
        always {
            script {
                if (fileExists('.github_deployment_id')) {
                    if (isUnix()) {
                        sh 'rm -f .github_deployment_id'
                    } else {
                        bat 'del /f /q .github_deployment_id'
                    }
                }
            }
        }
    }
}
