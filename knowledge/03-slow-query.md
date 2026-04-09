# 慢查询 (Slow Query)

## 定义

慢查询指执行时间超过预期阈值的 SQL 查询，通常由全表扫描、复杂关联、缺乏索引等原因导致。

## SQLite 性能基准

| 数据量级 | 可接受查询时间 |
|---------|--------------|
| < 1,000 | < 10ms |
| < 10,000 | < 50ms |
| < 100,000 | < 200ms |
| < 1,000,000 | < 1s |

## 分析方法

### 1. 使用 EXPLAIN QUERY PLAN

```sql
EXPLAIN QUERY PLAN 
SELECT * FROM orders 
WHERE user_id = 123 
ORDER BY created_at DESC;
```

### 2. 计时测量

```sql
.timer ON
SELECT * FROM orders WHERE status = 'delivered';
```

### 3. 分步分析

```sql
-- 分析每步的时间开销
.timer ON
SELECT COUNT(*) FROM orders;  -- 基线时间

.timer ON
SELECT * FROM orders WHERE user_id = 123;  -- 对比
```

## 常见慢查询模式

### 1. 大结果集排序

```sql
-- 慢：对大表全表排序
SELECT * FROM orders ORDER BY created_at DESC;

-- 快：使用索引 + LIMIT
SELECT * FROM orders ORDER BY id DESC LIMIT 100;
```

### 2. 复杂子查询

```sql
-- 慢：子查询在 WHERE 中
SELECT * FROM orders 
WHERE user_id IN (
    SELECT id FROM users WHERE created_at > '2024-01-01'
);

-- 快：改为 JOIN
SELECT o.* FROM orders o
JOIN users u ON o.user_id = u.id
WHERE u.created_at > '2024-01-01';
```

### 3. 不当使用聚合函数

```sql
-- 慢：对全表聚合
SELECT SUM(total_amount) FROM orders;

-- 快：先过滤再聚合
SELECT SUM(total_amount) FROM orders WHERE status = 'delivered';
```

### 4. 隐式类型转换

```sql
-- 慢：类型不匹配导致全表扫描
SELECT * FROM products WHERE price = '100';  -- price 是 REAL

-- 快：使用正确类型
SELECT * FROM products WHERE price = 100.0;
```

## 优化策略

### 策略一：添加 LIMIT

```sql
-- 添加分页限制
SELECT * FROM products LIMIT 100;
```

### 策略二：分解复杂查询

```sql
-- 分解为多个简单查询
-- 步骤1：获取用户最近订单
SELECT * FROM orders WHERE user_id = 123 ORDER BY created_at DESC LIMIT 10;

-- 步骤2：获取这些订单的详情
SELECT * FROM order_items WHERE order_id IN (1, 2, 3, ...);
```

### 策略三：使用物化视图/汇总表

```sql
-- 预先计算汇总数据
CREATE TABLE daily_sales AS
SELECT DATE(created_at) as date, SUM(total_amount) as total
FROM orders
GROUP BY DATE(created_at);

-- 查询变得很快
SELECT * FROM daily_sales WHERE date = '2024-01-01';
```

### 策略四：避免 SELECT *

```sql
-- 慢：查询所有字段
SELECT * FROM users WHERE email = 'test@example.com';

-- 快：只查询需要的字段
SELECT id, name, email FROM users WHERE email = 'test@example.com';
```

## SQLite 特定优化

### 1. 使用 PRAGMA

```sql
-- 开启查询优化器
PRAGMA query_only = OFF;

-- 设置缓存大小
PRAGMA cache_size = 10000;
```

### 2. 事务批量写入

```sql
-- 慢：逐条插入
INSERT INTO logs VALUES (1, 'message');
INSERT INTO logs VALUES (2, 'message');
-- ...

-- 快：事务批量插入
BEGIN TRANSACTION;
INSERT INTO logs VALUES (1, 'message');
INSERT INTO logs VALUES (2, 'message');
-- ...
COMMIT;
```

### 3. 分析表统计信息

```sql
-- 更新统计信息帮助优化器
ANALYZE;
```

## 检查清单

- [ ] 是否使用了 EXPLAIN 分析查询计划？
- [ ] 是否有不必要的全表扫描？
- [ ] 是否可以添加 LIMIT 限制结果集？
- [ ] 子查询是否可以改为 JOIN？
- [ ] 是否只查询需要的字段？
- [ ] 数据类型是否匹配？
- [ ] 是否需要创建索引？
