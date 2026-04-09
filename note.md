# SQL 性能问题测试数据库

## 数据库位置
`database/ecommerce.db`

## 表结构

### users
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| email | TEXT | 邮箱（无索引） |
| name | TEXT | 姓名 |
| created_at | TEXT | 创建时间 |

### orders
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| user_id | INTEGER | 用户ID（无索引） |
| total_amount | REAL | 订单金额 |
| status | TEXT | 订单状态 |
| created_at | TEXT | 创建时间（无索引） |

### order_items
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| order_id | INTEGER | 订单ID（无索引） |
| product_id | INTEGER | 产品ID |
| quantity | INTEGER | 数量 |
| price | REAL | 价格 |

### products
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | TEXT | 产品名 |
| category | TEXT | 分类（无索引） |
| price | REAL | 价格 |
| stock | INTEGER | 库存 |
| description | TEXT | 描述 |

## 性能问题 SQL

### 1. 全表扫描：邮箱查询（缺失索引）
```sql
SELECT * FROM users WHERE email = 'user123@example.com';
```
**问题**：`email`字段无索引，邮箱查询需全表扫描

### 2. 全表扫描：用户订单查询（缺失索引）
```sql
SELECT * FROM orders WHERE user_id = 123;
```
**问题**：`user_id`字段无索引，用户所有订单需全表扫描

### 3. 慢查询：日期范围查询（缺失索引）
```sql
SELECT * FROM orders WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31';
```
**问题**：`created_at`字段无索引，日期范围扫描全表

### 4. SELECT * + 全表扫描：订单详情
```sql
SELECT * FROM order_items WHERE order_id = 456;
```
**问题**：`order_id`无索引，且使用SELECT * 查询所有字段

### 5. 缺乏分页：分类产品查询（全表扫描）
```sql
SELECT * FROM products WHERE category = 'electronics';
```
**问题**：`category`无索引，且无LIMIT分页，全表返回

### 6. N+1 问题：查询用户及其订单
```sql
-- 第一条查询用户
SELECT * FROM users WHERE id = 1;
-- 后续N条查询该用户每个订单（应用层循环）
SELECT * FROM orders WHERE user_id = 1;
```
**问题**：需在应用层循环查询，每个用户订单都是一次全表扫描

### 7. 慢查询：订单金额统计
```sql
SELECT user_id, SUM(total_amount), COUNT(*) 
FROM orders 
WHERE status = 'delivered' 
GROUP BY user_id;
```
**问题**：`status`字段无索引，需全表扫描后排序分组

### 8. SELECT * 问题：产品列表
```sql
SELECT * FROM products WHERE price > 100;
```
**问题**：使用SELECT * 查询所有字段，但实际可能只需id、name、price
