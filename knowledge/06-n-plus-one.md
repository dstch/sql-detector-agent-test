# N+1 查询问题 (N+1 Query Problem)

## 定义

N+1 问题指在查询数据时，先执行 1 次查询获取主数据，然后对每条主数据执行 N 次关联查询。

## 示例

### 问题代码

```python
# 第 1 次查询：获取所有订单
orders = db.execute("SELECT * FROM orders WHERE user_id = 123")

# N 次查询：获取每条订单的用户信息
for order in orders:
    order.user = db.execute(
        "SELECT * FROM users WHERE id = ?", 
        order.user_id
    )
```

### 生成的 SQL

```sql
-- 第 1 条 SQL：获取订单
SELECT * FROM orders WHERE user_id = 123;  -- 假设返回 50 条

-- 后续 50 条 SQL：获取每条订单的用户
SELECT * FROM users WHERE id = 1;
SELECT * FROM users WHERE id = 2;
SELECT * FROM users WHERE id = 3;
-- ... 共 50 次
```

## 性能对比

| 方案 | SQL 执行次数 | 耗时 |
|------|------------|------|
| N+1 查询 | 51 | ~500ms |
| JOIN 查询 | 1 | ~50ms |
| 批量 IN 查询 | 2 | ~60ms |

## 常见场景

### 1. 循环中查询关联数据

```python
# 问题
users = db.query("SELECT * FROM users")
for user in users:
    user.order_count = db.query(
        f"SELECT COUNT(*) FROM orders WHERE user_id = {user.id}"
    )

# SQL 执行：1 + N 次
```

### 2. ORM 延迟加载

```python
# SQLAlchemy 默认行为
orders = session.query(Order).limit(100).all()
for order in orders:
    # 每次访问 user 属性都会触发一次查询
    print(order.user.name)

# 实际 SQL：1 + 100 次
```

### 3. API 序列化

```python
# 获取文章列表，每篇文章获取作者信息
articles = db.query("SELECT * FROM articles LIMIT 100")
for article in articles:
    article.author = db.query(
        "SELECT * FROM users WHERE id = ?", 
        article.author_id
    )
```

## 解决方案

### 方案一：使用 JOIN

```sql
SELECT o.*, u.name as user_name, u.email as user_email
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.user_id = 123;
```

### 方案二：批量 IN 查询

```sql
-- 第 1 步：获取订单
SELECT * FROM orders WHERE user_id = 123;

-- 第 2 步：批量获取用户
SELECT * FROM users WHERE id IN (1, 2, 3, 4, 5, ...);
```

### 方案三：Eager Loading（ORM）

```python
# SQLAlchemy Eager Loading
from sqlalchemy.orm import joinedload

orders = session.query(Order).options(
    joinedload(Order.user)
).limit(100).all()

# 只执行 1 条 SQL，自动填充 user 属性
for order in orders:
    print(order.user.name)  # 不再触发额外查询
```

### 方案四：子查询

```sql
SELECT o.*, 
       (SELECT name FROM users WHERE id = o.user_id) as user_name
FROM orders o
WHERE o.user_id = 123;
```

## 循环查询 vs JOIN 对比

```python
# 方案 A：循环查询（N+1）
for order in orders:
    user = db.get_user(order.user_id)
    
# 方案 B：JOIN
users = db.get_users_for_orders(orders)

# 方案 C：IN 批量查询
user_ids = [o.user_id for o in orders]
users = db.get_users_by_ids(user_ids)
```

## 检测 N+1 问题

### 日志分析

```python
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel('INFO')
```

### EXPLAIN 分析

```sql
-- 如果看到多个 SCAN 或 SEARCH，说明可能有问题
EXPLAIN QUERY PLAN SELECT * FROM orders;
EXPLAIN QUERY PLAN SELECT * FROM users WHERE id = 1;
```

### Django Debug Toolbar

```python
# Django 项目
INSTALLED_APPS = [
    'debug_toolbar',
]
```

## 检查清单

- [ ] 循环中是否有数据库查询？
- [ ] ORM 是否使用了延迟加载？
- [ ] 是否可以用 JOIN 替代多次查询？
- [ ] 是否可以用批量 IN 查询？
- [ ] 是否有未使用 eager loading 的关联查询？
