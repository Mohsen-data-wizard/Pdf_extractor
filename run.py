#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 اسکریپت اجرای سریع سیستم استخراج هوشمند اسناد گمرکی
توسعهدهنده: Mohsen-data-wizard
تاریخ: 2025-06-05
"""

import sys
import os
import subprocess
from pathlib import Path

def check_dependencies():
    """بررسی وابستگیها"""
    
    required_packages = [
        'tkinter',
        'customtkinter', 
        'PIL',
        'cv2',
        'numpy',
        'fitz',
        'easyocr',
        'pandas',
        'openpyxl'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            elif package == 'customtkinter':
                import customtkinter
            elif package == 'PIL':
                from PIL import Image
            elif package == 'cv2':
                import cv2
            elif package == 'numpy':
                import numpy
            elif package == 'fitz':
                import fitz
            elif package == 'easyocr':
                import easyocr
            elif package == 'pandas':
                import pandas
            elif package == 'openpyxl':
                import openpyxl
                
        except ImportError:
            missing_packages.append(package)
            
    return missing_packages

def install_missing_packages(packages):
    """نصب پکیجهای گمشده"""
    
    package_map = {
        'tkinter': 'tkinter',
        'customtkinter': 'customtkinter>=5.2.0',
        'PIL': 'Pillow>=10.0.0',
        'cv2': 'opencv-python>=4.8.0',
        'numpy': 'numpy>=1.24.0',
        'fitz': 'PyMuPDF>=1.23.0',
        'easyocr': 'easyocr>=1.7.0',
        'pandas': 'pandas>=2.0.0',
        'openpyxl': 'openpyxl>=3.1.0'
    }
    
    for package in packages:
        if package == 'tkinter':
            print(f"⚠️ {package} باید با Python نصب باشد")
            continue
            
        pip_package = package_map.get(package, package)
        
        try:
            print(f"📦 نصب {pip_package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_package])
            print(f"✅ {pip_package} نصب شد")
        except subprocess.CalledProcessError:
            print(f"❌ خطا در نصب {pip_package}")
            
def check_files():
    """بررسی وجود فایلهای اصلی"""
    
    required_files = [
        'main.py',
        'extractor_engine.py', 
        'learning_system.py'
    ]
    
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
            
    return missing_files

def create_directories():
    """ایجاد پوشههای مورد نیاز"""
    
    directories = ['patterns', 'temp', 'results', 'uploads', 'assets']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)

def main():
    """تابع اصلی"""
    
    print("=" * 60)
    print("🎯 سیستم استخراج هوشمند اسناد گمرکی")
    print("👨💻 توسعهدهنده: Mohsen-data-wizard")
    print("📅 نسخه: 2.0 | تاریخ: 2025-06-05")
    print("=" * 60)
    
    # بررسی فایلها
    print("🔍 بررسی فایلهای اصلی...")
    missing_files = check_files()
    
    if missing_files:
        print("❌ فایلهای زیر یافت نشد:")
        for file in missing_files:
            print(f"   - {file}")
        print("لطفا فایلها را کامل دانلود کنید.")
        return
    else:
        print("✅ تمام فایلهای اصلی موجود است")
    
    # بررسی وابستگیها
    print("\n🔍 بررسی وابستگیها...")
    missing_packages = check_dependencies()
    
    if missing_packages:
        print("❌ پکیجهای زیر یافت نشد:")
        for package in missing_packages:
            print(f"   - {package}")
            
        choice = input("\n❓ آیا میخواهید آنها را نصب کنید (y/n): ").lower()
        
        if choice in ['y', 'yes', 'بله']:
            install_missing_packages(missing_packages)
            
            # بررسی مجدد
            missing_packages = check_dependencies()
            if missing_packages:
                print("❌ برخی پکیجها نصب نشدند. لطفا دستی نصب کنید.")
                return
        else:
            print("❌ نصب لغو شد.")
            return
    else:
        print("✅ تمام وابستگیها موجود است")
    
    # ایجاد پوشهها
    print("\n📁 ایجاد پوشهها...")
    create_directories()
    print("✅ پوشهها آماده است")
    
    # اجرای برنامه
    print("\n🚀 راهاندازی برنامه...")
    print("=" * 60)
    
    try:
        from main import CustomsExtractorGUI
        
        print("🎉 برنامه با موفقیت اجرا شد!")
        print("📝 راهنمای استفاده را در README.md مطالعه کنید")
        print("=" * 60)
        
        app = CustomsExtractorGUI()
        app.run()
        
    except ImportError as e:
        print(f"❌ خطا در وارد کردن ماولها: {e}")
        print("لطفا مجددا وابستگیها را نصب کنید:")
        print("   python install.py")
        
    except Exception as e:
        print(f"❌ خطا در اجرای برنامه: {e}")
        print("برای گزارش مشکل با توسعهدهنده تماس بگیرید.")

if __name__ == "__main__":
    main()
