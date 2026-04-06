# Hướng Dẫn Chạy Trên VSCode

## Yêu Cầu Trước Khi Chạy

- Python 3.10 trở lên đã cài đặt
- VSCode đã mở thư mục `xosomn-xosomt`

---

## Bước 1 — Cài Thư Viện (Chỉ Làm 1 Lần)

Mở terminal trong VSCode (nhấn **Ctrl + `**), chạy:

```bash
python -m pip install -r requirements.txt
```

Chờ cài xong (khoảng 1-2 phút).

---

## Bước 2 — Chạy Lấy Dữ Liệu

### Lấy dữ liệu hôm nay

```bash
python src/main_xsmn.py
python src/main_xsmt.py
```

### Lấy dữ liệu một khoảng ngày cụ thể

```bash
python src/main_xsmn.py --from 2026-01-01 --to 2026-04-04
python src/main_xsmt.py --from 2026-01-01 --to 2026-04-04
```

### Lấy toàn bộ lịch sử từ đầu đến nay (chạy lâu ~2 tiếng)

```bash
python src/main_xsmn.py --all
python src/main_xsmt.py --all
```

---

## Bước 3 — Kiểm Tra Kết Quả

Sau khi chạy xong, kiểm tra các thư mục:

| Thư mục | Nội dung |
|---------|----------|
| `data/xsmn/` | File CSV và JSON của XSMN |
| `data/xsmt/` | File CSV và JSON của XSMT |
| `images/xsmn/` | Biểu đồ phân tích XSMN |
| `images/xsmt/` | Biểu đồ phân tích XSMT |

---

## Bước 4 — Đẩy Dữ Liệu Lên GitHub

Sau khi có dữ liệu, đẩy lên GitHub để lưu trữ:

```bash
git add .
git commit -m "data: cap nhat du lieu xo so"
git pull --rebase origin main
git push
```

---

## Lịch Chạy Tự Động Trên GitHub

Hệ thống đã cài đặt **tự động chạy hàng ngày** qua GitHub Actions:

| Workflow | Giờ chạy | Khu vực |
|----------|----------|---------|
| Daily Fetch XSMN | 17:00 giờ VN | Miền Nam |
| Daily Fetch XSMT | 17:05 giờ VN | Miền Trung |

Bạn **không cần làm gì thêm** — dữ liệu tự động cập nhật mỗi ngày sau 17:00.

---

## Xử Lý Lỗi Thường Gặp

### Lỗi: `ModuleNotFoundError`
```bash
python -m pip install -r requirements.txt
```

### Lỗi: `python` không nhận dạng được
Thay `python` bằng `python3`:
```bash
python3 src/main_xsmn.py
```

### Lỗi: Không tìm thấy đài nào
Kiểm tra kết nối internet, rồi chạy lại.

### Lỗi git push bị từ chối
```bash
git pull --rebase origin main
git push
```
