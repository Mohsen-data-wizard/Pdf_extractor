#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 اسکریپت نصب سیستم استخراج هوشمند اسناد گمرکی
توسعهدهنده: Mohsen-data-wizard
تاریخ: 2025-06-05
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """نصب وابستگیها"""
    
    print("🚀 شروع نصب وابستگیها...")
    
    # لیست پکیجهای اصلی
    packages = [
        "customtkinter>=5.2.0",
        "Pillow>=10.0.0", 
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "PyMuPDF>=1.23.0",
        "easyocr>=1.7.0",
        "pandas>=2.0.0",
        "openpyxl>=3.1.0"
    ]
    
    # نصب هر پکیج
    for package in packages:
        try:
            print(f"📦 نصب {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} نصب شد")
        except subprocess.CalledProcessError as e:
            print(f"❌ خطا در نصب {package}: {e}")
            
def create_directories():
    """ایجاد پوشههای مورد نیاز"""
    
    print("📁 ایجاد پوشهها...")
    
    directories = [
        "patterns",
        "temp", 
        "results",
        "uploads",
        "assets"
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(exist_ok=True)
            print(f"✅ پوشه {directory} ایجاد شد")
        except Exception as e:
            print(f"❌ خطا در ایجاد پوشه {directory}: {e}")
            
def create_config_file():
    """ایجاد فایل تنظیمات پیشفرض"""
    
    print("⚙️ ایجاد فایل تنظیمات...")
    
    config = {
        "confidence_threshold": 0.35,
        "dpi": 300,
        "languages": {
            "fa": True,
            "en": True,
            "ar": True
        },
        "theme": "light",
        "auto_save": True,
        "learning_enabled": True,
        "created_at": "2025-06-05",
        "version": "2.0"
    }
    
    try:
        import json
        with open("settings.json", 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print("✅ فایل تنظیمات ایجاد شد")
    except Exception as e:
        print(f"❌ خطا در ایجاد تنظیمات: {e}")
        
def check_system_requirements():
    """بررسی سیستم"""
    
    print("🔍 بررسی سیستم...")
    
    # بررسی ورن Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 یا بالاتر مورد نیاز است")
        return False
    else:
        print(f"✅ Python {sys.version}")
        
    # بررسی pip
    try:
        import pip
        print("✅ pip موجود است")
    except ImportError:
        print("❌ pip یافت نشد")
        return False
        
    return True
    
def main():
    """تابع اصلی نصب"""
    
    print("=" * 50)
    print("🎯 سیستم استخراج هوشمند اسناد گمرکی")
    print("👨💻 توسعهدهنده: Mohsen-data-wizard")
    print("📅 نسخه: 2.0")
    print("=" * 50)
    
    # بررسی سیستم
    if not check_system_requirements():
        print("❌ سیستم شما نیازمندیها را برآورده نمیکند")
        return
        
    # نصب وابستگیها
    install_requirements()
    
    # ایجاد پوشهها
    create_directories()
    
    # ایجاد تنظیمات
    create_config_file()
    
    print("\n" + "=" * 50)
    print("🎉 نصب با موفقیت تکمیل شد!")
    print("🚀 برای اجرا دستور زیر را وارد کنید:")
    print("   python main.py")
    print("=" * 50)

if __name__ == "__main__":
    main()
