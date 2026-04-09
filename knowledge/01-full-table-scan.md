# 全表扫描 (Full Table Scan)

## 定义

全表扫描是指数据库引擎必须读取表中**所有行**才能找到符合条件的记录，而不是利用索引快速定位。

## 识别方法

### SQLite EXPLAIN QUERY PLAN

```sql
EXPLAIN QUERY PLAN SELECT * FROM users WHERE email = 'test@example.com';
```

**全表扫描特征输出**：
```
SCAN table_name
```

**索引查找特征输出**：
```
SEARCH table_name USING INDEX index_name
```

## 常见原因

### 1. WHERE 条件字段无索引

```sql
-- 触发全表扫描
SELECT * FROM orders WHERE user_id = 123;

-- 原因：user_id 字段无索引
```

### 2. LIKE 模糊匹配以通配符开头

```sql
-- 全表扫描
SELECT * FROM products WHERE name LIKE '%phone%';

-- 可用索引（如果以固定前缀开始）
SELECT * FROM products WHERE name LIKE 'phone%';
```

### 3. OR 条件使用不同字段

```sql
-- 全表扫描（通常情况）
SELECT * FROM users WHERE email = 'a@b.com' OR phone = '123456';

-- 优化：拆分为 UNION
SELECT * FROM users WHERE email = 'a@b.com'
UNION ALL
SELECT * FROM users WHERE phone = '123456' AND email <> 'a@b.com';
```

### 4. 数据类型不匹配

```sql
-- 如果 user_id 是 INTEGER
SELECT * FROM orders WHERE user_id = '123';  -- 字符串导致全表扫描

-- 正确写法
SELECT * FROM orders WHERE user_id = 123;
```

## 性能影响

| 表数据量 | 全表扫描耗时 | 索引查询耗时 |
|---------|------------|------------|
| 1,000   | ~5ms       | ~1ms       |
| 10,000  | ~50ms      | ~1ms       |
| 100,000 | ~500ms     | ~2ms       |
| 1,000,000| ~5s      | ~3ms       |

## 解决方案

### 1. 创建合适索引

```sql
-- 为 WHERE 条件字段创建索引
CREATE INDEX idx_orders_user_id ON orders(user_id);
```

### 2. 优化查询条件

```sql
-- 避免使用函数
-- 全表扫描
SELECT * FROM orders WHERE UPPER(status) = 'PAID';

-- 优化
SELECT * FROM orders WHERE status = 'PAID';
```

### 3. 使用覆盖索引

```sql
-- 查询只需返回 id, name
SELECT id, name FROM users WHERE email = 'test@example.com';

-- 创建覆盖索引
CREATE INDEX idx_users_email ON users(email) INCLUDE (id, name);
```

## 检查清单

- [ ] WHERE 子句字段是否有索引？
- [ ] LIKE 模式是否以通配符开头？
- [ ] OR 条件是否可以转换为 UNION？
- [ ] 数据类型是否匹配？
- [ ] 是否可以对结果集先过滤再关联？
