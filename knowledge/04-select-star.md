# SELECT * 问题

## 定义

`SELECT *` 会查询表的所有字段，包括不必要的列，增加 I/O 和网络传输开销。

## 性能影响

```sql
-- 表结构：users (id, email, name, phone, address, created_at, updated_at, ...)
-- 需要：id, email, name

-- 浪费：额外 5 个字段的查询和传输
SELECT * FROM users WHERE id = 1;

-- 高效：只查询需要的 3 个字段
SELECT id, email, name FROM users WHERE id = 1;
```

## 常见问题场景

### 1. 应用层只需要部分字段

```python
# 数据库返回所有字段
result = db.execute("SELECT * FROM users WHERE id = ?", user_id)
# 但应用只使用 name
print(result.name)
```

### 2. 关联查询返回冗余字段

```sql
-- orders 和 users 各有 created_at, updated_at
SELECT * FROM orders o
JOIN users u ON o.user_id = u.id;
-- 结果中包含两个表的重复时间字段
```

### 3. 获取关联数据

```sql
-- 只需要订单 ID 和金额
SELECT * FROM orders WHERE user_id = 123;

-- 应该写成
SELECT id, total_amount FROM orders WHERE user_id = 123;
```

## 解决方案

### 方案一：明确列出字段

```sql
-- 只列出需要的字段
SELECT id, email, name FROM users WHERE id = 1;
```

### 方案二：使用覆盖索引

```sql
-- 索引包含所有需要的数据，无需回表
CREATE INDEX idx_users_email ON users(email) INCLUDE (id, name);
```

### 方案三：拆分为多个查询

```sql
-- 第一步：获取基本信息
SELECT id, email FROM users WHERE email = 'test@example.com';

-- 第二步：需要更多字段时再查询
SELECT profile_data FROM user_profiles WHERE user_id = ?;
```

## ORM 中的问题

### SQLAlchemy

```python
# 问题：默认查询所有字段
User.query.filter_by(id=1).first()

# 解决：明确指定字段
db.session.query(User.id, User.email, User.name).filter_by(id=1).first()
# 或
db.session.query(User).with_entities(User.id, User.email, User.name).filter_by(id=1).first()
```

### Django ORM

```python
# 问题
User.objects.get(id=1)

# 解决：使用 only() 指定字段
User.objects.only('id', 'email', 'name').get(id=1)
```

## 适用 SELECT * 的场景

1. **INSERT ... SELECT**：源表结构明确
   ```sql
   INSERT INTO users_backup SELECT * FROM users;
   ```

2. **CREATE TABLE ... AS SELECT**：快速创建表
   ```sql
   CREATE TABLE temp_orders AS SELECT * FROM orders WHERE status = 'draft';
   ```

3. **调试/探索性查询**：快速查看数据
   ```sql
   SELECT * FROM orders LIMIT 5;  -- 探索数据结构
   ```

## 检查清单

- [ ] 是否只查询需要的字段？
- [ ] 关联查询是否重复返回了相同的字段？
- [ ] 是否可以利用覆盖索引避免回表？
- [ ] 应用层是否使用了所有返回的字段？
- [ ] 对于简单查询，可以拆分为多个精确查询吗？
