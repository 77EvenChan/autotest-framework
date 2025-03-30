// Jenkinsfile — Jenkins Pipeline 配置
// 适用于企业内网 Jenkins 环境

pipeline {
    agent any  // 在任意可用节点执行

    // 环境变量 — 敏感信息用 Jenkins Credentials 管理
    environment {
        DATABASE_URL = credentials('taskflow-db-url')  // Jenkins 凭据 ID
        REDIS_URL    = 'redis://redis:6379/0'
        JWT_SECRET   = credentials('taskflow-jwt-secret')
    }

    // 构建工具
    tools {
        python 'Python3.11'  // Jenkins 全局工具配置中的 Python 名称
    }

    // Pipeline 阶段
    stages {

        // ──── 阶段 1：拉取代码 ────
        stage('拉取代码') {
            steps {
                checkout scm  // 从 Git 拉取代码
            }
        }

        // ──── 阶段 2：安装依赖 ────
        stage('安装依赖') {
            steps {
                sh '''
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install -r sut/requirements.txt
                '''
            }
        }

        // ──── 阶段 3：启动服务 ────
        stage('启动服务') {
            steps {
                // 用 Docker Compose 启动 MySQL + Redis + SUT
                sh 'docker-compose up -d'
                sh 'sleep 10'  // 等待服务就绪
            }
        }

        // ──── 阶段 4：运行测试 ────
        stage('运行测试') {
            steps {
                sh 'python -m pytest tests/ -v --tb=short --junitxml=reports/junit.xml'
            }
            // 测试失败时继续执行后续阶段（不要中断 Pipeline）
            post {
                always {
                    // 发布 JUnit 测试报告
                    junit 'reports/junit.xml'
                }
            }
        }

        // ──── 阶段 5：生成报告 ────
        stage('生成报告') {
            steps {
                sh '''
                    # 生成 Allure 报告数据
                    python -m pytest tests/ --alluredir=reports/allure-results
                '''
            }
            post {
                always {
                    // 发布 Allure 报告（需要安装 Allure Jenkins 插件）
                    allure([
                        results: [[path: 'reports/allure-results']],
                        report: 'reports/allure-report'
                    ])
                }
            }
        }
    }

    // Pipeline 完成后的清理
    post {
        always {
            // 停止 Docker 容器
            sh 'docker-compose down'
            // 清理工作空间
            cleanWs()
        }
        success {
            echo '✅ 测试全部通过！'
        }
        failure {
            echo '❌ 测试失败，请检查报告。'
        }
    }
}
