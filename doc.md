# Nếu muốn tải đúng phiên bản

```javascript
pip download websockets==10.4 -d wheels
```

### Vẫn dùng websockets 10.4

Vì `websockets 10.4` là thư viện Python thuần, Thầy có thể tải source:

```javascript
pip download websockets==10.4 --no-binary=:all:
```

# Tự động tải tất cả dependency của một package

pip download some_package -d wheels