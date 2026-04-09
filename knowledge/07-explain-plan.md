# 执行计划分析 (EXPLAIN QUERY PLAN)

## 概述

`EXPLAIN QUERY PLAN` 显示数据库如何执行查询，包括是否使用索引、是否全表扫描等信息。

## SQLite 输出格式

```sql
EXPLAIN QUERY PLAN SELECT * FROM users WHERE email = 'test@example.com';
```

### 输出列

| 列 | 说明 |
|----|------|
| id | 步骤编号 |
| parent | 父步骤编号 |
| notused | 0=使用，1=未使用（查询优化器决定） |
| detail | 执行详情 |

## 关键操作标识

### 全表扫描

```
SCAN table_name
```
**含义**：读取表中所有行
**问题**：性能差，应尽量避免

### 索引扫描

```
SEARCH table_name USING INDEX index_name
```
**含义**：使用索引快速查找
**性能**：良好

### 索引扫描（多次）

```
SEARCH table_name USING INDEX index_name FOR EACH ROW
```
**含义**：索引扫描并回表
**性能**：取决于回表次数

### 排序

```
USE TEMP B-TREE FOR ORDER BY
```
**含义**：需要临时数据结构排序
**优化**：创建相应索引可消除

## 常见场景分析

### 场景 1：全表扫描

```sql
EXPLAIN QUERY PLAN 
SELECT * FROM users WHERE email = 'test@example.com';

-- 输出
id  parent  notused  detail
--- ------  -------  ---------------------------
2   0       0        SCAN users
```

**问题**：email 字段无索引
**解决**：`CREATE INDEX idx_users_email ON users(email);`

### 场景 2：索引查找

```sql
CREATE INDEX idx_users_email ON users(email);

EXPLAIN QUERY PLAN 
SELECT * FROM users WHERE email = 'test@example.com';

-- 输出
id  parent  notused  detail
--- ------  -------  ---------------------------
2   0       0        SEARCH users USING INDEX idx_users_email
```

**性能**：良好

### 场景 3：组合条件

```sql
CREATE INDEX idx_orders_status_user ON orders(status, user_id);

EXPLAIN QUERY PLAN 
SELECT * FROM orders WHERE status = 'paid' AND user_id = 123;

-- 输出
id  parent  notused  detail
--- ------  -------  ---------------------------
2   0       0        SEARCH orders USING INDEX idx_orders_status_user
```

**性能**：良好

### 场景 4：JOIN 操作

```sql
EXPLAIN QUERY PLAN 
SELECT * FROM orders o 
JOIN users u ON o.user_id = u.id 
WHERE u.email = 'test@example.com';

-- 输出
id  parent  notused  detail
--- ------  -------  ---------------------------
3   0       0        SEARCH users USING INDEX idx_users_email
4   3       0        SEARCH orders USING INDEX idx_orders_user_id
```

**性能**：良好（两个表都使用索引）

### 场景 5：子查询

```sql
EXPLAIN QUERY PLAN 
SELECT * FROM orders 
WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@example.com');

-- 输出
id  parent  notused  detail
--- ------  -------  ---------------------------
2   0       0        SCAN orders
3   2       0        SCAN users
```

**问题**：全表扫描
**优化**：考虑改为 JOIN

### 场景 6：排序操作

```sql
EXPLAIN QUERY PLAN 
SELECT * FROM orders ORDER BY created_at DESC;

-- 输出
id  parent  notused  detail
--- ------  -------  ---------------------------
1   0       0        SCAN orders
2   0       0        USE TEMP B-TREE FOR ORDER BY
```

**问题**：内存排序
**优化**：`CREATE INDEX idx_orders_created_at ON orders(created_at);`

## 优化器决策因素

SQLite 查询优化器根据以下因素决定执行计划：

1. **统计信息**：表大小、索引选择性
2. **索引可用性**：是否有可用索引
3. **查询复杂度**：JOIN、子查询等
4. **数据分布**：WHERE 条件的选择性

## 强制使用特定索引

```sql
-- SQLite 可以通过 SQL 提示强制使用索引
SELECT * FROM users USE INDEX (idx_users_email) WHERE email = 'test@example.com';

-- 忽略特定索引
SELECT * FROM users IGNORE INDEX (idx_users_email) WHERE email = 'test@example.com';
```

## 分析步骤

1. **识别慢查询**：找出执行时间长的 SQL
2. **查看执行计划**：使用 EXPLAIN QUERY PLAN
3. **识别问题模式**：
   - `SCAN` = 全表扫描（需要优化）
   - `USE TEMP B-TREE` = 内存排序（考虑加索引）
   - 多层嵌套 = 复杂子查询（考虑改写）
4. **验证优化效果**：修改后重新分析

## 常用查询模板

```sql
-- 分析单表查询
EXPLAIN QUERY PLAN SELECT * FROM table WHERE col = ?;

-- 分析 JOIN
EXPLAIN QUERY PLAN SELECT * FROM t1 JOIN t2 ON t1.id = t2.t1_id;

-- 分析聚合
EXPLAIN QUERY PLAN SELECT COUNT(*), col FROM table GROUP BY col;

-- 分析排序
EXPLAIN QUERY PLAN SELECT * FROM table ORDER BY col;
```

## 检查清单

- [ ] 查询是否使用了 `SCAN`？是否需要创建索引？
- [ ] 是否有 `USE TEMP B-TREE FOR ORDER BY`？是否可以通过索引消除？
- [ ] JOIN 是否都使用了索引？
- [ ] 子查询是否可以改为 JOIN？
- [ ] 索引是否被实际使用（`notused` 列）？
