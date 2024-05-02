pipeline {
    agent {
        any
        // dockerfile {
        //     filename 'jenkins/Dockerfile'
        //     args '-v /var/run/docker.sock:/var/run/docker.sock'
        // }
    }

    environment {
        HOME="."
        AWS_DEFAULT_REGION = 'us-west-2'
        ECR_REPO_NAME = 'my-ecr-repo'
        DOCKER_IMAGE_TAG = 'latest'
    }

    stages {
        stage('Prepare') {
            steps {
                checkout scm
                script {
                    sh '''
                    echo "Building $BRANCH_NAME"
                    echo "Building $TAG_NAME"

                    chmod +x sam_train.sh 
                    chmod +x sam_deploy.sh 
                    chmod +x sam_monitor.sh 

                    pip install awscli

                    python -m poetry config virtualenvs.create false
                    python -m poetry lock --no-update
                    python -m poetry install --all-extras
                    '''
                }
            }
        }
        stage('Install SAM CLI') {
            steps {
                script {
                    // Check if sam cli is installed
                    def samCliInstalled = sh(script: 'command -v sam', returnStatus: true) == 0

                    // Install SAM CLI 
                    if (!samCliInstalled){
                        sh 'yum install -y unzip zip'
                        sh 'curl -sL "https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip" -o sam.zip'
                        sh 'unzip sam.zip -d /tmp/'
                        sh 'sudo /tmp/install'
                    }
                }
            }
        }

        stage('Test') {
            steps {
                withAWS([role: 'arn_for_service_role', region: 'us-west-2']) {
                    script {
                        sh '''
                        poetry config virtualenvs.create false
                        poetry run pytest --ruff --html=build-reports/tests/report.html --self-contained-html \
                            --junitxml=build-reports/tests/report.xml \
                            --cov-report html:build-reports/coverage/html \
                            --cov-report xml:build-reports/coverage/coverage.xml \
                            --cov=repo_name
                        '''
                    }
                }    
            }
            
        }


        stage('Build Docker Image') {
            steps {
                // Assume IAM role
                withAWS([role: 'arn_for_service_role', region: 'us-west-2']) {
                    // Authenticate with ECR
                    sh "aws ecr get-login-password --region ${AWS_DEFAULT_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com"

                    // Build the Docker image
                    sh "docker build -t ${ECR_REPO_NAME}:${DOCKER_IMAGE_TAG} ."
                }
            }
        }

        stage('Push Docker Image to ECR') {
            steps {
                // Assume IAM role
                withCredentials([iamRole(credentialsId: 'aws-iam-role', roleArn: 'arn:aws:iam::123456789012:role/service-role/my-iam-role')]) {
                    // Tag the Docker image with ECR repository URI
                    sh "docker tag ${ECR_REPO_NAME}:${DOCKER_IMAGE_TAG} ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${ECR_REPO_NAME}:${DOCKER_IMAGE_TAG}"
                    
                    // Push the Docker image to ECR
                    sh "docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${ECR_REPO_NAME}:${DOCKER_IMAGE_TAG}"
                }
            }
        }


        stage('SAM deploy Model Train job') {
            steps {
                sh 'sam_train.sh'
            }
        }

        stage('SAM deploy Model Deployment with Autoscaling job') {
            steps {
                sh 'sam_deploy.sh'
            }
        }

        stage('SAM deploy Sagemaker Model Monitor job') {
            steps {
                sh 'sam_monitor.sh'
            }
        }


        stage('SonarQube') {
            steps {
                withCerberus([
                    sdbPath: 'app/path-to-sonarqube-creds/sonarqube',
                    sdbKeys: [
                        'token': 'SONAR_TOKEN',
                        'host': 'SONAR_HOST_URL'
                    ]
                ]) {
                    sh "/var/opt/sonar-scanner-cli/bin/sonar-scanner"
                }
            }
        }


        stage('Release') {
            when {
                expression {
                    env.BRANCH_NAME == 'main'
                    }
            }
            steps {
                script {
                    withCerberus(
                        [
                            sdbPath: 'app/path-to-creds/artifactory-credentials',
                            sdbKeys: [
                                'artifactory-user' : 'ARTIFACTORY_USER',
                                'artifactory-password': 'ARTIFACTORY_PASSWORD'
                            ]
                        ]
                    ) {
                        sh '''
                        poetry build
                        poetry publish -r artifactory -u "${ARTIFACTORY_USER}" -p "${ARTIFACTORY_PASSWORD}"
                        '''
                    }
                }
            }
        }


    }


}




