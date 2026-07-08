-- ============================================
-- Career Coach 数据库初始化脚本
-- ============================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS `career_coach`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE `career_coach`;

-- ============================================
-- 用户表
-- ============================================
CREATE TABLE IF NOT EXISTS `users` (
    `id`            BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '主键，用户 ID',
    `username`      VARCHAR(50)      NOT NULL                 COMMENT '登录用户名，唯一',
    `password`      VARCHAR(255)     NOT NULL                 COMMENT '加密后的密码',
    `nickname`      VARCHAR(50)      NOT NULL DEFAULT ''      COMMENT '昵称/显示名称',
    `avatar_url`    VARCHAR(500)     NOT NULL DEFAULT ''      COMMENT '头像 OSS 地址',
    `status`        TINYINT          NOT NULL DEFAULT 1       COMMENT '状态：1=正常, 0=禁用',
    `created_at`    DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP           COMMENT '创建时间',
    `updated_at`    DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  COMMENT '更新时间',
    `last_login_at` DATETIME         NULL     DEFAULT NULL   COMMENT '最后登录时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    KEY `idx_status` (`status`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================
-- 对话表
-- ============================================
CREATE TABLE IF NOT EXISTS `conversations` (
    `id`              BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '主键，对话 ID',
    `user_id`         BIGINT UNSIGNED  NOT NULL                 COMMENT '所属用户 ID',
    `resume_id`       BIGINT UNSIGNED  NULL     DEFAULT NULL    COMMENT '关联简历 ID',
    `title`           VARCHAR(100)     NOT NULL DEFAULT '新对话' COMMENT '对话标题',
    `message_count`   INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '消息总数',
    `last_message_at` DATETIME         NULL     DEFAULT NULL    COMMENT '最近一条消息时间',
    `created_at`      DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP           COMMENT '创建时间',
    `updated_at`      DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_updated` (`user_id`, `updated_at` DESC),
    KEY `idx_last_message_at` (`last_message_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话表';

-- ============================================
-- 消息表
-- ============================================
CREATE TABLE IF NOT EXISTS `messages` (
    `id`              BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '主键，消息 ID',
    `conversation_id` BIGINT UNSIGNED  NOT NULL                 COMMENT '所属对话 ID',
    `role`            VARCHAR(20)      NOT NULL                 COMMENT '角色：user / assistant / system',
    `content`         TEXT             NOT NULL                 COMMENT '消息内容',
    `prompt_tokens`   INT              NULL     DEFAULT NULL    COMMENT '输入 token 数（仅 assistant 消息）',
    `completion_tokens` INT            NULL     DEFAULT NULL    COMMENT '输出 token 数（仅 assistant 消息）',
    `created_at`      DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP  COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_conversation_created` (`conversation_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息表';

-- ============================================
-- 简历表
-- ============================================
CREATE TABLE IF NOT EXISTS `resumes` (
    `id`            BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '主键，简历 ID',
    `user_id`       BIGINT UNSIGNED  NOT NULL                 COMMENT '所属用户 ID',
    `filename`      VARCHAR(255)     NOT NULL                 COMMENT '原始文件名',
    `file_url`      VARCHAR(500)     NOT NULL                 COMMENT '文件访问地址',
    `raw_text`      TEXT             NULL     DEFAULT NULL    COMMENT '解析后的简历纯文本',
    `target_jd`     TEXT             NULL     DEFAULT NULL    COMMENT '目标岗位 JD 文本（可选）',
    `suggestions`    JSON             NULL     DEFAULT NULL    COMMENT '结构化优化建议列表',
    `ability_profile` JSON           NULL     DEFAULT NULL    COMMENT '能力评估结果',
    `tier_suggestion` JSON           NULL     DEFAULT NULL    COMMENT '梯队建议',
    `retrieved_jds`  JSON             NULL     DEFAULT NULL    COMMENT '检索到的 JD 列表',
    `score_assessment` JSON           NULL     DEFAULT NULL    COMMENT '评分报告（综合评分+技能维度评分）',
    `dimension_report` JSON           NULL     DEFAULT NULL    COMMENT '维度分析报告（4维度+战略建议）',
    `total_issues`  INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '问题总数（冗余字段）',
    `created_at`    DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP  COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_created` (`user_id`, `created_at` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='简历表';

-- ============================================
-- JD 知识库元数据表
-- ============================================
CREATE TABLE IF NOT EXISTS `jd_knowledge` (
    `id`             BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '主键，JD ID',
    `company`        VARCHAR(100)     NOT NULL                 COMMENT '公司名称',
    `position`       VARCHAR(100)     NOT NULL                 COMMENT '岗位名称',
    `tier`           VARCHAR(20)      NOT NULL                 COMMENT '梯队：startup/mid/big_edge/big_core',
    `tech_direction` VARCHAR(20)      NOT NULL                 COMMENT '技术方向：后端/前端/算法/数据/全栈/测试/运维',
    `requirements`   TEXT             NOT NULL                 COMMENT '岗位要求正文（用于向量化与检索）',
    `source_url`     VARCHAR(500)     NOT NULL DEFAULT ''      COMMENT 'JD 来源链接',
    `vector_indexed` TINYINT          NOT NULL DEFAULT 0       COMMENT '是否已向量化：1=是 0=否',
    `created_at`     DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP  COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_tier` (`tier`),
    KEY `idx_tech_direction` (`tech_direction`),
    KEY `idx_vector_indexed` (`vector_indexed`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='JD 知识库元数据表';

-- ============================================
-- 测验会话表
-- ============================================
CREATE TABLE IF NOT EXISTS `quiz_sessions` (
    `id`                BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '主键，测验会话 ID',
    `user_id`           BIGINT UNSIGNED  NOT NULL                 COMMENT '所属用户 ID',
    `conversation_id`   BIGINT UNSIGNED  NOT NULL                 COMMENT '关联的对话 ID',
    `title`             VARCHAR(100)     NOT NULL                 COMMENT '测验标题（用户输入）',
    `target_jd`         TEXT             NULL     DEFAULT NULL    COMMENT 'JD 上下文快照',
    `question_count`    INT UNSIGNED     NOT NULL DEFAULT 8       COMMENT '题目数量',
    `user_requirements` TEXT             NULL     DEFAULT NULL    COMMENT '用户自定义要求',
    `status`            VARCHAR(20)      NOT NULL DEFAULT 'in_progress' COMMENT 'in_progress / completed',
    `score`             INT UNSIGNED     NULL     DEFAULT NULL    COMMENT '总分（答对数）',
    `report`            JSON             NULL     DEFAULT NULL    COMMENT '评估报告',
    `created_at`        DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP  COMMENT '创建时间',
    `updated_at`        DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_updated` (`user_id`, `updated_at` DESC),
    KEY `idx_conversation_id` (`conversation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测验会话表';

-- ============================================
-- 测验题目表
-- ============================================
CREATE TABLE IF NOT EXISTS `quiz_questions` (
    `id`                BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '主键，题目 ID',
    `session_id`        BIGINT UNSIGNED  NOT NULL                 COMMENT '所属测验会话 ID',
    `stem`              TEXT             NOT NULL                 COMMENT '题目题干',
    `options`           JSON             NOT NULL                 COMMENT '选项列表 [{id, label, text, description}]',
    `correct_option_id` VARCHAR(10)      NOT NULL                 COMMENT '正确答案选项 ID',
    `explanation`       TEXT             NOT NULL                 COMMENT '正确答案的详细解释',
    `topic_tags`        JSON             NULL     DEFAULT NULL    COMMENT '主题标签',
    `category`          VARCHAR(20)      NULL     DEFAULT NULL    COMMENT 'basic / project / behavioral',
    `user_answer`       VARCHAR(10)      NULL     DEFAULT NULL    COMMENT '用户选择的选项 ID',
    `is_correct`        TINYINT(1)       NULL     DEFAULT NULL    COMMENT '用户是否答对',
    `order_index`       INT UNSIGNED     NOT NULL                 COMMENT '题目序号',
    `created_at`        DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP  COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_session_order` (`session_id`, `order_index`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测验题目表';

