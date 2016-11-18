node {
    withCredentials([
        [$class: 'StringBinding', credentialsId: 'AWS_ACCESS_KEY_ID', variable: 'AWS_ACCESS_KEY_ID'],
        [$class: 'StringBinding', credentialsId: 'AWS_SECRET_ACCESS_KEY', variable: 'AWS_SECRET_ACCESS_KEY'],
    ]) {
        stage('Checkout') { checkout scm }
        def githubNotifier = load('github-status-notifier')

        try {
            stage('Build') {
                sh "sudo docker build -t $IMAGE_NAME ."
            }

            stage('Deploy') {
                sh """
                   sudo docker run -e AWS_ACCESS_KEY_ID=${env.AWS_ACCESS_KEY_ID} \
                                   -e AWS_SECRET_ACCESS_KEY=${env.AWS_SECRET_ACCESS_KEY} \
                                   -e AWS_DEFAULT_REGION=${env.AWS_DEFAULT_REGION} \
                                   --rm $IMAGE_NAME
                """
            }
            githubNotifier.success()
            slackSend color: 'good', message: "${env.JOB_NAME} ${env.BUILD_NUMBER} (<${env.BUILD_URL}|Open>)"
        } catch (e) {
            currentBuild.result = 'FAILURE'
            githubNotifier.error()
            slackSend color: 'danger', message: "${env.JOB_NAME} ${env.BUILD_NUMBER} (<${env.BUILD_URL}|Open>)"
        }

    }
}
