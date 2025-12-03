# استفاده از ایمیج رسمی پایتون
FROM python:3.11-slim

# تنظیم پوشه کاری داخل کانتینر
WORKDIR /app

# کپی کردن فایل نیازمندی‌ها و نصب آن‌ها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کردن بقیه کدهای پروژه
COPY . .

# پورت ۸۰۰۱ را باز کن (اگرچه مستقیماً استفاده نمی‌شود، اما تمرین خوبی است)
EXPOSE 8001