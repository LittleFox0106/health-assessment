# 健康测评系统 - Health Assessment System

> 全栈开发挑战项目 | FastAPI + SQLite + 静态前端

## 快速启动

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动服务

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 访问应用

- **前端页面**: http://localhost:8000
- **API 文档 (Swagger)**: http://localhost:8000/docs
- **API 文档 (ReDoc)**: http://localhost:8000/redoc

---

## API 接口文档

### 基础信息

- **Base URL**: `/api/v1`
- **认证方式**: `X-Session-Token` 请求头
- **响应格式**: `{ "code": 200, "message": "success", "data": {...} }`

### 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/users/init` | 初始化用户，生成 session_token |
| POST | `/api/v1/sessions` | 创建测评会话 |
| GET | `/api/v1/sessions/{id}/progress` | 获取会话进度（进度恢复） |
| PATCH | `/api/v1/sessions/{id}/step/1` | 保存第 1 步：性别 + 目标 |
| PATCH | `/api/v1/sessions/{id}/step/2` | 保存第 2 步：年龄 + 身高 + 体重 |
| PATCH | `/api/v1/sessions/{id}/step/3` | 保存第 3 步：目标体重 + 运动频率 |
| POST | `/api/v1/sessions/{id}/submit` | 提交所有数据，触发计算 |
| GET | `/api/v1/sessions/{id}/result` | 获取测评结果（差异化返回） |
| POST | `/api/v1/pay` | 模拟支付回调 |
| GET | `/api/v1/subscription/status` | 查询订阅状态 |

---

## cURL 调用示例

### 完整流程演示

```bash
# 1. 初始化用户
curl -X POST http://localhost:8000/api/v1/users/init

# 响应示例：
# {
#   "code": 200,
#   "message": "用户初始化成功",
#   "data": {
#     "user_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
#     "session_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
#   }
# }

# 2. 创建会话（替换 TOKEN 为上一步返回的 session_token）
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "X-Session-Token: TOKEN"

# 3. 保存第 1 步（替换 SESSION_ID）
curl -X PATCH http://localhost:8000/api/v1/sessions/SESSION_ID/step/1 \
  -H "X-Session-Token: TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"gender": "male", "goal": "lose_weight"}'

# 4. 保存第 2 步
curl -X PATCH http://localhost:8000/api/v1/sessions/SESSION_ID/step/2 \
  -H "X-Session-Token: TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"age": 28, "height_cm": 175, "weight_kg": 80}'

# 5. 保存第 3 步
curl -X PATCH http://localhost:8000/api/v1/sessions/SESSION_ID/step/3 \
  -H "X-Session-Token: TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target_weight_kg": 70, "exercise_frequency": "3-5_times"}'

# 6. 提交测评
curl -X POST http://localhost:8000/api/v1/sessions/SESSION_ID/submit \
  -H "X-Session-Token: TOKEN"

# 7. 查看结果（非会员 - 高级数据为 null）
curl http://localhost:8000/api/v1/sessions/SESSION_ID/result \
  -H "X-Session-Token: TOKEN"

# 8. 模拟支付
curl -X POST http://localhost:8000/api/v1/pay \
  -H "X-Session-Token: TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "USER_ID"}'

# 9. 再次查看结果（会员 - 完整数据）
curl http://localhost:8000/api/v1/sessions/SESSION_ID/result \
  -H "X-Session-Token: TOKEN"
```

### Postman 导入

访问 http://localhost:8000/openapi.json 可获取 OpenAPI 规范，直接导入 Postman。

---

## 数据库 Schema

### ER 关系

```
users (1) ──< (N) assessment_sessions
users (1) ──< (1) subscriptions
assessment_sessions (1) ──< (1) assessment_data
```

### 表结构

**users**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | 用户唯一标识 |
| session_token | VARCHAR(64) UNIQUE | 会话令牌 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**assessment_sessions**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | 会话唯一标识 |
| user_id | VARCHAR(36) FK | 关联用户 |
| current_step | SMALLINT | 当前步骤 (1-4) |
| status | VARCHAR(20) | in_progress/completed/abandoned |
| created_at | DATETIME | 创建时间 |
| completed_at | DATETIME | 完成时间 |

**assessment_data**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | 主键 |
| session_id | VARCHAR(36) FK UNIQUE | 关联会话 |
| gender | VARCHAR(10) | 性别 |
| goal | VARCHAR(50) | 目标 |
| age | SMALLINT | 年龄 (1-120) |
| height_cm | DECIMAL(5,1) | 身高 (50-300) |
| weight_kg | DECIMAL(5,1) | 体重 (20-500) |
| target_weight_kg | DECIMAL(5,1) | 目标体重 |
| exercise_frequency | VARCHAR(30) | 运动频率 |
| bmi_value | DECIMAL(5,2) | BMI 值 |
| bmi_category | VARCHAR(20) | BMI 分类 |
| bmr | DECIMAL(7,1) | 基础代谢率 |
| tdee | DECIMAL(7,1) | 每日总能量消耗 |
| daily_calorie_intake | SMALLINT | 建议每日摄入 |
| target_prediction_days | SMALLINT | 目标预测天数 |
| protein_g / carbs_g / fat_g | DECIMAL(6,1) | 宏量营养素 |

**subscriptions**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | 主键 |
| user_id | VARCHAR(36) FK UNIQUE | 关联用户 |
| status | VARCHAR(20) | active/expired/cancelled |
| plan_type | VARCHAR(30) | 订阅计划 |
| started_at | DATETIME | 开始时间 |
| expires_at | DATETIME | 过期时间 |

---

## 健康评估算法

- **BMI**: 体重(kg) / 身高(m)²
- **BMR (Mifflin-St Jeor)**:
  - 男性: 10×体重 + 6.25×身高 - 5×年龄 + 5
  - 女性: 10×体重 + 6.25×身高 - 5×年龄 - 161
- **TDEE**: BMR × 活动系数 (1.2/1.375/1.55/1.725)
- **每日摄入**: TDEE + 目标调整 (-500/+300/0/-200 kcal)
- **预测天数**: |目标体重-当前体重| / 每周变化量 × 7

---

## 差异化返回策略

| 数据字段 | 非会员 | 会员 |
|----------|--------|------|
| BMI 值/分类 | ✅ | ✅ |
| BMR/TDEE | ✅ | ✅ |
| 建议摄入量 | ✅ | ✅ |
| 目标预测天数 | ❌ null | ✅ |
| 营养素分解 | ❌ null | ✅ |
| 每周变化量 | ❌ null | ✅ |

---

## 技术栈

- **后端**: FastAPI (Python 3.10+) + SQLAlchemy 2.0
- **数据库**: SQLite (开发) / PostgreSQL + Supabase (生产)
- **前端**: 原生 HTML/CSS/JS (FastAPI 静态托管)
- **部署**: Uvicorn ASGI Server

## 切换到 Supabase PostgreSQL

设置环境变量即可：

```bash
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
