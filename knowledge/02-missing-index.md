# 缺失索引 (Missing Index)

## 定义

索引是帮助数据库快速定位数据的结构。缺失索引指在 WHERE、JOIN、ORDER BY 子句中使用的字段没有建立相应索引。

## 何时需要创建索引

### 1. WHERE 条件字段

```sql
-- 高频查询条件字段应建索引
SELECT * FROM orders WHERE status = 'pending';
-- → CREATE INDEX idx_orders_status ON orders(status);
```

### 2. JOIN 关联字段

```sql
-- 外键字段应建索引
SELECT * FROM orders o JOIN users u ON o.user_id = u.id;
-- → CREATE INDEX idx_orders_user_id ON orders(user_id);
```

### 3. ORDER BY 排序字段

```sql
-- 经常排序的字段
SELECT * FROM products ORDER BY created_at DESC;
-- → CREATE INDEX idx_products_created_at ON products(created_at);
```

### 4. 组合索引优化

```sql
-- 经常同时作为条件的字段
SELECT * FROM orders WHERE status = 'paid' AND created_at > '2024-01-01';

-- 组合索引（顺序很重要！）
CREATE INDEX idx_orders_status_created ON orders(status, created_at);
```

## 索引设计原则

### 原则一：高选择性字段优先

```sql
-- 高选择性：唯一值多，如 user_id
SELECT * FROM orders WHERE user_id = 123;  -- 适合建索引

-- 低选择性：唯一值少，如 status（只有几个值）
SELECT * FROM orders WHERE status = 'paid';  -- 通常不适合单独建索引
```

### 原则二：最左前缀原则

```sql
-- 组合索引 (A, B, C)
-- 支持：A, AB, ABC
-- 不支持：BC, AC, C
```

### 原则三：覆盖索引减少回表

```sql
-- 只需返回 id, email
SELECT id, email FROM users WHERE email = 'test@example.com';

-- 创建覆盖索引
CREATE INDEX idx_users_email_covering ON users(email) INCLUDE (id);
```

## 索引类型选择

### SQLite 支持的索引类型

| 类型 | 语法 | 适用场景 |
|------|------|---------|
| 普通索引 | `CREATE INDEX idx ON t(col)` | 常规加速查询 |
| 唯一索引 | `CREATE UNIQUE INDEX idx ON t(col)` | 保证唯一性 + 加速 |
| 组合索引 | `CREATE INDEX idx ON t(col1, col2)` | 多字段组合查询 |
| 覆盖索引 | `CREATE INDEX idx ON t(col) INCLUDE (col2)` | 减少回表 |

## 索引不是越多越好

- **写操作变慢**：每次 INSERT/UPDATE/DELETE 需要更新索引
- **占用空间**：索引占用额外磁盘空间
- **维护成本**：索引需要定期重建

## 判断是否需要索引

### 使用 EXPLAIN 分析

```sql
EXPLAIN QUERY PLAN SELECT * FROM orders WHERE user_id = 123;
-- 如果显示 SCAN，应为 user_id 创建索引
```

### 评估查询频率

```sql
-- 查询计划被执行的频率
SELECT sql, count(*) as exec_count 
FROM sqlite_stat1 
GROUP BY sql;
```

## 创建索引最佳实践

```sql
-- 1. 为高频查询创建索引
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- 2. 为外键创建索引（提升 JOIN 性能）
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);

-- 3. 为经常排序的字段创建索引
CREATE INDEX idx_products_price ON products(price);

-- 4. 组合索引遵循最左前缀
CREATE INDEX idx_orders_status_date ON orders(status, created_at);
```

## 检查清单

- [ ] WHERE 条件高频查询字段是否有索引？
- [ ] 外键字段是否都建了索引？
- [ ] ORDER BY 字段是否建了索引？
- [ ] 组合索引顺序是否正确？
- [ ] 是否可以考虑覆盖索引减少回表？
- [ ] 索引是否过于冗余？
