# 缺乏分页 (No Pagination)

## 定义

查询返回大量结果集而没有使用 LIMIT 或 OFFSET 进行分页，导致数据库和网络传输额外开销。

## 性能影响

```sql
-- 返回全部 5000 条订单
SELECT * FROM orders WHERE user_id = 123;
-- 结果：5000 rows returned (耗时 500ms)

-- 只返回前 100 条
SELECT * FROM orders WHERE user_id = 123 LIMIT 100;
-- 结果：100 rows returned (耗时 50ms)
```

## 常见问题模式

### 1. API 返回大列表

```sql
-- 后端代码
orders = db.execute("SELECT * FROM orders")
return jsonify(orders)  # 返回全部，可能是 10 万条
```

### 2. 前端无限滚动

```javascript
// 每次滚动加载更多，但请求没有 LIMIT
fetch('/api/orders')  // 返回全部
```

### 3. 数据导出

```sql
-- 导出全表
SELECT * FROM orders INTO OUTFILE 'orders.csv';  -- 可能是百万级
```

## 解决方案

### 方案一：使用 LIMIT/OFFSET

```sql
-- 第 1 页（1-100）
SELECT id, total_amount, status, created_at 
FROM orders 
WHERE user_id = 123 
ORDER BY created_at DESC 
LIMIT 100 OFFSET 0;

-- 第 2 页（101-200）
SELECT id, total_amount, status, created_at 
FROM orders 
WHERE user_id = 123 
ORDER BY created_at DESC 
LIMIT 100 OFFSET 100;
```

### 方案二：基于键值的分页（更高效）

```sql
-- 利用上次查询的最后一条 ID
SELECT id, total_amount, status, created_at 
FROM orders 
WHERE user_id = 123 AND id > 1000
ORDER BY id ASC 
LIMIT 100;
```

### 方案三：游标分页（最高效）

```sql
-- 使用 created_at 作为游标（需索引）
SELECT id, total_amount, status, created_at 
FROM orders 
WHERE user_id = 123 
  AND created_at < '2024-01-15 10:30:00'
ORDER BY created_at DESC 
LIMIT 100;
```

## OFFSET 的陷阱

```sql
-- 问题：OFFSET 越大，数据库扫描越多
SELECT * FROM orders LIMIT 100 OFFSET 10000;
-- 数据库仍需扫描 10000+100 条记录

-- 解决：使用键值分页
SELECT * FROM orders 
WHERE id > (SELECT id FROM orders ORDER BY id LIMIT 1 OFFSET 10000)
LIMIT 100;
```

## 前端配合

```javascript
// 错误：加载全部
const loadOrders = async () => {
  const res = await fetch('/api/orders');
  const orders = await res.json();
  renderOrders(orders);
};

// 正确：分页加载
const loadOrdersPage = async (page) => {
  const res = await fetch(`/api/orders?page=${page}&limit=100`);
  const { data, hasMore } = await res.json();
  renderOrders(data);
  return hasMore;
};
```

## API 设计建议

```json
// 响应格式
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 100,
    "total": 5000,
    "has_more": true
  }
}
```

## 默认值设置

```sql
-- 始终添加 LIMIT
SELECT * FROM products;
-- 等同于
SELECT * FROM products LIMIT 18446744073709551615;  -- SQLite 最大值

-- 建议设置合理的默认 LIMIT
SELECT id, name, price FROM products LIMIT 100;
```

## 检查清单

- [ ] 查询是否添加了 LIMIT？
- [ ] LIMIT 值是否合理？
- [ ] 是否考虑了 OFFSET 性能问题？
- [ ] API 是否支持分页参数？
- [ ] 是否可以使用游标分页代替 OFFSET？
- [ ] 大数据导出是否有特殊处理？
