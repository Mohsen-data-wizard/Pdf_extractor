#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 موتور استخراج اسناد گمرکی
توسعهدهنده: محسن 
تاریخ: 2025-06-05
"""

import cv2
import numpy as np
import easyocr
import fitz  # PyMuPDF
import re
import json
from pathlib import Path
import logging
from PIL import Image
import time
from typing import Dict, List, Any, Optional

class DocumentExtractor:
    def __init__(self):
        """موتور استخراج پیشرفته"""
        
        # تنظیم logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # تنظیمات پیشفرض
        self.config = {
            'confidence_threshold': 0.35,
            'device': 'cpu',
            'languages': ['fa', 'en', 'ar'],
            'dpi': 300,
            'enhance_image': True
        }
        
        # راهاندازی OCR
        self.setup_ocr()
        
        # الگوهای فیلدها
        self.setup_field_patterns()
        
        # نوعهای سند پشتیبانی شده
        self.document_types = {
            'import_single': 'واردات تککالایی',
            'import_multi': 'واردات چندکالایی', 
            'export_single': 'صادرات تککالایی',
            'export_multi': 'صادرات چندکالایی'
        }
        
        # کش برای نتایج OCR
        self.ocr_cache = {}
        
    def setup_ocr(self):
        """راهاندازی موتور OCR"""
        try:
            self.logger.info("🔄 راهاندازی OCR...")
            
            self.ocr_reader = easyocr.Reader(
                self.config['languages'],
                gpu=False,
                verbose=False,
                download_enabled=True
            )
            
            self.logger.info("✅ OCR آماده است")
            
        except Exception as e:
            self.logger.error(f"❌ خطا در راهاندازی OCR: {e}")
            raise
            
    def setup_field_patterns(self):
        """تنظیم الگوهای استخراج فیلدها - نسخه پیشرفته"""
        
        # الگوهای پایه برای اسناد وارداتی
        self.import_patterns = {
            "شماره_کوتا": {
                "patterns": [
                    r"کوتا[\s\)]*(\d{8,9})",
                    r"(\d{8,9})\s*ش[\s\.]*بایگانی",
                    r"شماره\s*ثبت[\s\(]*کوتا[\s\)]*(\d{8,9})",
                    r"(\d{8,9})\s*تاریخ",
                    r"(\d{8,9})\s*۱۴۰۳",
                    r"(\d{8,9})\s*1403",
                    r"کوتا[\s:]*(\d{8,9})",
                    r"شماره[\s:]*(\d{8,9})\s*کوتا",
                    r"(\d{8,9})\s*شماره\s*کوتا"
                ],
                "validation": lambda x: x.isdigit() and len(x) >= 8,
                "description": "شماره کوتا 8-9 رقمی",
                "priority": 1
            },
            
            "کد_کالا": {
                "patterns": [
                    r"33[\s\.]*کد\s*کالا[\s:]*(\d{8})",
                    r"کد\s*کالا[\s:]*(\d{8})",
                    r"(\d{8})\s*کشور\s*سازنده",
                    r"33[\s\.]*(\d{8})",
                    r"(\d{8})\s*شرح",
                    r"HS\s*Code[\s:]*(\d{8})",
                    r"Commodity\s*Code[\s:]*(\d{8})",
                    r"کد[\s:]*(\d{8})\s*کالا",
                    r"(\d{8})\s*کد\s*کالا",
                    r"33[\s\.]*کد[\s:]*(\d{8})"
                ],
                "validation": lambda x: x.isdigit() and len(x) == 8,
                "description": "کد 8 رقمی کالا",
                "priority": 1
            },
            
            "شرح_کالا": {
                "patterns": [
                    r"31[\s\.]*شرح\s*کالا[\s:]*([^\n\r\d]{5,100})",
                    r"شرح\s*کالا[\s:]*([^\n\r\d]{5,100})",
                    r"31[\s\.]*([^\n\r\d]{10,100})\s*نوع\s*بسته",
                    r"توضیحات[\s:]*([^\n\r\d]{5,100})",
                    r"31[\s\.]*([آ-ی\s]{5,100})\s*\d",
                    r"شرح[\s:]*([آ-ی\s]{5,100})",
                    r"31[\s\.]*([A-Za-z\s]{5,100})\s*[Pp]ack"
                ],
                "validation": lambda x: len(x.strip()) >= 3 and not x.isdigit(),
                "description": "شرح کالا",
                "priority": 2
            },
            
            "نوع_بسته": {
                "patterns": [
                    r"نوع\s*بسته[\s:]*([^\d\n\r]{2,20})",
                    r"31[\s\.]*.*نوع\s*بسته[\s:]*([^\d\n\r]{2,20})",
                    r"بسته\s*بندی[\s:]*([^\d\n\r]{2,20})",
                    r"[Pp]ackage[\s:]*([A-Za-z\s]{2,20})",
                    r"([کارتن|جعبه|بسته|کیسه|گونی])",
                    r"نوع[\s:]*([آ-ی\s]{2,15})\s*تعداد"
                ],
                "validation": lambda x: len(x.strip()) >= 2 and not x.isdigit(),
                "description": "نوع بستهبندی",
                "priority": 3
            },
            
            "تعداد_بسته": {
                "patterns": [
                    r"تعداد\s*بسته[\s:]*(\d+)",
                    r"31[\s\.]*.*تعداد[\s:]*(\d+)",
                    r"(\d+)\s*عدد\s*بسته",
                    r"تعداد[\s:]*(\d+)\s*[کارتن|جعبه|بسته]",
                    r"(\d+)\s*[کارتن|جعبه|بسته]",
                    r"تعداد[\s:]*(\d+)"
                ],
                "validation": lambda x: x.isdigit() and int(x) > 0,
                "description": "تعداد بسته",
                "priority": 3
            },
            
            "وزن_خالص": {
                "patterns": [
                    r"38[\s\.]*وزن\s*خالص[\s:]*(\d+(?:\.\d+)?)",
                    r"وزن\s*خالص[\s:]*(\d+(?:\.\d+)?)",
                    r"خالص[\s:]*(\d+(?:\.\d+)?)",
                    r"Net\s*Weight[\s:]*(\d+(?:\.\d+)?)",
                    r"(\d+(?:\.\d+)?)\s*کیلو",
                    r"(\d+(?:\.\d+)?)\s*KG",
                    r"38[\s\.]*(\d+(?:\.\d+)?)\s*کیلو",
                    r"وزن[\s:]*(\d+(?:\.\d+)?)\s*کیلوگرم",
                    r"(\d+(?:\.\d+)?)\s*کیلوگرم"
                ],
                "validation": lambda x: x.replace('.', '').replace(',', '').isdigit() and float(x) > 0,
                "description": "وزن خالص",
                "priority": 2
            },
            
            "کشور_طرف_معامله": {
                "patterns": [
                    r"17[\s\.]*کشور\s*طرف\s*معامله[\s:]*([A-Za-z\u0600-\u06FF\s]{2,30})",
                    r"کشور\s*طرف\s*معامله[\s:]*([A-Za-z\u0600-\u06FF\s]{2,30})",
                    r"17[\s\.]*کشور[\s:]*([A-Za-z\u0600-\u06FF\s]{2,30})",
                    r"Country[\s:]*([A-Za-z\s]{2,30})",
                    r"Origin[\s:]*([A-Za-z\s]{2,30})",
                    r"17[\s\.]*([A-Za-z]{2,20})\s*\d",
                    r"کشور[\s:]*([آ-ی\s]{2,20})"
                ],
                "validation": lambda x: len(x.strip()) >= 2 and not x.isdigit(),
                "description": "کشور طرف معامله",
                "priority": 2
            },
            
            "نرخ_ارز": {
                "patterns": [
                    r"23[\s\.]*نرخ\s*ارز[\s:]*(\d+(?:\.\d+)?)",
                    r"نرخ\s*ارز[\s:]*(\d+(?:\.\d+)?)",
                    r"23[\s\.]*نرخ[\s:]*(\d+(?:\.\d+)?)",
                    r"Rate[\s:]*(\d+(?:\.\d+)?)",
                    r"exchange\s*rate[\s:]*(\d+(?:\.\d+)?)",
                    r"23[\s\.]*(\d+(?:\.\d+)?)\s*ریال",
                    r"نرخ[\s:]*(\d+(?:\.\d+)?)"
                ],
                "validation": lambda x: x.replace('.', '').replace(',', '').isdigit() and float(x) > 0,
                "description": "نرخ ارز",
                "priority": 3
            },
            
            "نوع_ارز": {
                "patterns": [
                    r"22[\s\.]*نوع\s*ارز[\s:]*([A-Z]{2,4})",
                    r"نوع\s*ارز[\s:]*([A-Z]{2,4})",
                    r"Currency[\s:]*([A-Z]{2,4})",
                    r"22[\s\.]*([A-Z]{2,4})\s*نرخ",
                    r"ارز[\s:]*([A-Z]{2,4})",
                    r"([USD|EUR|IRR|AED]{3})"
                ],
                "validation": lambda x: len(x.strip()) >= 2 and x.isupper(),
                "description": "نوع ارز",
                "priority": 4
            },
            
            "نوع_معامله": {
                "patterns": [
                    r"24[\s\.]*نوع\s*معامله[\s:]*(\d{1,3})",
                    r"نوع\s*معامله[\s:]*(\d{1,3})",
                    r"24[\s\.]*(\d{1,3})\s*نوع",
                    r"معامله[\s:]*(\d{1,3})"
                ],
                "validation": lambda x: x.isdigit() and len(x) <= 3,
                "description": "نوع معامله",
                "priority": 4
            },
            
            "بیمه": {
                "patterns": [
                    r"37[\s\.]*بیمه[\s:]*(\d+(?:\.\d+)?)",
                    r"بیمه[\s:]*(\d+(?:\.\d+)?)",
                    r"Insurance[\s:]*(\d+(?:\.\d+)?)",
                    r"بیمه[\s:]*(\d+(?:\.\d+)?)\s*کرایه",
                    r"(\d+(?:\.\d+)?)\s*بیمه",
                    r"37[\s\.]*(\d+(?:\.\d+)?)\s*بیمه"
                ],
                "validation": lambda x: x.replace('.', '').replace(',', '').isdigit(),
                "description": "مبلغ بیمه",
                "priority": 3
            },
            
            "کرایه": {
                "patterns": [
                    r"کرایه[\s:]*(\d+(?:\.\d+)?)",
                    r"37[\s\.]*کرایه[\s:]*(\d+(?:\.\d+)?)",
                    r"Freight[\s:]*(\d+(?:\.\d+)?)",
                    r"بیمه.*کرایه[\s:]*(\d+(?:\.\d+)?)",
                    r"(\d+(?:\.\d+)?)\s*کرایه",
                    r"کرایه[\s:]*(\d+(?:\.\d+)?).*37"
                ],
                "validation": lambda x: x.replace('.', '').replace(',', '').isdigit(),
                "description": "مبلغ کرایه",
                "priority": 3
            },
            
            "تعداد_واحد_کالا": {
                "patterns": [
                    r"41[\s\.]*تعداد\s*واحد\s*کالا[\s:]*(\d+(?:\.\d+)?)",
                    r"تعداد\s*واحد\s*کالا[\s:]*(\d+(?:\.\d+)?)",
                    r"41[\s\.]*تعداد[\s:]*(\d+(?:\.\d+)?)",
                    r"واحد\s*کالا[\s:]*(\d+(?:\.\d+)?)",
                    r"41[\s\.]*(\d+(?:\.\d+)?)\s*واحد"
                ],
                "validation": lambda x: x.replace('.', '').replace(',', '').isdigit() and float(x) > 0,
                "description": "تعداد واحد کالا",
                "priority": 3
            },
            
            "ارزش_قلم_کالا": {
                "patterns": [
                    r"42[\s\.]*ارزش\s*قلم\s*کالا[\s:]*(\d+(?:\.\d+)?)",
                    r"ارزش\s*قلم\s*کالا[\s:]*(\d+(?:\.\d+)?)",
                    r"42[\s\.]*مبلغ\s*کل\s*فاکتور[\s:]*(\d+(?:\.\d+)?)",
                    r"مبلغ\s*کل\s*فاکتور[\s:]*(\d+(?:\.\d+)?)",
                    r"42[\s\.]*(\d+(?:\.\d+)?)\s*ارزش",
                    r"ارزش[\s:]*(\d+(?:\.\d+)?)\s*قلم"
                ],
                "validation": lambda x: x.replace('.', '').replace(',', '').isdigit() and float(x) > 0,
                "description": "ارزش قلم کالا",
                "priority": 2
            },
            
            "ارزش_گمرکی": {
                "patterns": [
                    r"46[\s\.]*ارزش\s*گمرکی[\s:]*(\d+(?:\.\d+)?)",
                    r"ارزش\s*گمرکی[\s:]*(\d+(?:\.\d+)?)",
                    r"Customs\s*Value[\s:]*(\d+(?:\.\d+)?)",
                    r"CIF[\s:]*(\d+(?:\.\d+)?)",
                    r"46[\s\.]*(\d+(?:\.\d+)?)\s*ارزش",
                    r"گمرکی[\s:]*(\d+(?:\.\d+)?)"
                ],
                "validation": lambda x: x.replace('.', '').replace(',', '').isdigit() and float(x) > 0,
                "description": "ارزش گمرکی",
                "priority": 2
            },
            
            "مبلغ_حقوق_ورودی": {
                "patterns": [
                    r"041[\s\.]*.*مبلغ[\s:]*(\d+(?:\.\d+)?)",
                    r"حقوق\s*ورودی[\s:]*(\d+(?:\.\d+)?)",
                    r"041.*(\d+(?:\.\d+)?).*مبلغ",
                    r"مبلغ[\s:]*(\d+(?:\.\d+)?)\s*041",
                    r"ورودی[\s:]*(\d+(?:\.\d+)?)",
                    r"041[\s\.]*(\d+(?:\.\d+)?)"
                ],
                "validation": lambda x: x.replace('.', '').replace(',', '').isdigit(),
                "description": "مبلغ حقوق ورودی",
                "priority": 3
            },
            
            "مالیات_بر_ارزش_افزوده": {
                "patterns": [
                    r"047[\s\.]*.*مبلغ[\s:]*(\d+(?:\.\d+)?)",
                    r"مالیات\s*بر\s*ارزش\s*افزوده[\s:]*(\d+(?:\.\d+)?)",
                    r"047.*(\d+(?:\.\d+)?).*مبلغ",
                    r"مبلغ[\s:]*(\d+(?:\.\d+)?)\s*047",
                    r"ارزش\s*افزوده[\s:]*(\d+(?:\.\d+)?)",
                    r"047[\s\.]*(\d+(?:\.\d+)?)"
                ],
                "validation": lambda x: x.replace('.', '').replace(',', '').isdigit(),
                "description": "مالیات بر ارزش افزوده",
                "priority": 3
            },
            
            "جمع_حقوق_عوارض": {
                "patterns": [
                    r"جمع\s*حقوق\s*و\s*عوارض[\s:]*(\d+(?:\.\d+)?)",
                    r"049[\s\.]*.*جمع[\s:]*(\d+(?:\.\d+)?)",
                    r"Total[\s:]*(\d+(?:\.\d+)?)",
                    r"جمع[\s:]*(\d+(?:\.\d+)?)\s*049",
                    r"حقوق\s*و\s*عوارض[\s:]*(\d+(?:\.\d+)?)",
                    r"049[\s\.]*(\d+(?:\.\d+)?)"
                ],
                "validation": lambda x: x.replace('.', '').replace(',', '').isdigit(),
                "description": "جمع حقوق و عوارض",
                "priority": 3
            }
        }
        
        # الگوهای ویه برای صفحات چندکالایی
        self.multi_item_patterns = {
            "کالا_اول": {
                "شرح_کالا": r"31[\s\.]*([آ-ی\s]{5,100}).*?(?=31[\s\.]*[آ-ی]|$)",
                "کد_کالا": r"33[\s\.]*(\d{8}).*?(?=33[\s\.]*\d{8}|$)",
                "وزن_خالص": r"38[\s\.]*(\d+(?:\.\d+)?).*?(?=38[\s\.]*\d|$)"
            },
            "کالا_دوم": {
                "شرح_کالا": r"31[\s\.]*[آ-ی\s]{5,100}.*?31[\s\.]*([آ-ی\s]{5,100})",
                "کد_کالا": r"33[\s\.]*\d{8}.*?33[\s\.]*(\d{8})",
                "وزن_خالص": r"38[\s\.]*\d+(?:\.\d+)?.*?38[\s\.]*(\d+(?:\.\d+)?)"
            }
        }
        
        # الگوهای صادراتی (مشابه وارداتی با تنظیمات جزئی)
        self.export_patterns = self.import_patterns.copy()
        
    def detect_document_type(self, text: str) -> str:
        """تشخیص نوع سند - بهبود یافته"""
        
        text_lower = text.lower()
        
        # کلمات کلیدی برای تشخیص
        import_keywords = ['واردات', 'import', 'ورود', 'کوتا', 'وارد']
        export_keywords = ['صادرات', 'export', 'خروج', 'صادر']
        
        # شمارش کلمات
        import_count = sum(1 for word in import_keywords if word in text_lower)
        export_count = sum(1 for word in export_keywords if word in text_lower)
        
        # تشخیص نوع (واردات/صادرات)
        is_import = import_count >= export_count
        
        # تشخیص تککالایی/چندکالایی - روش پیشرفته
        multi_indicators = 0
        
        # جستجو برای الگوهای تکراری
        patterns_to_check = [
            (r'کد\s*کالا', 'کد کالا'),
            (r'33[\s\.]*\d{8}', 'کد کالا'),
            (r'شرح\s*کالا', 'شرح کالا'),
            (r'31[\s\.]*[آ-ی]', 'شرح فارسی'),
            (r'وزن\s*خالص', 'وزن خالص'),
            (r'38[\s\.]*\d+', 'وزن')
        ]
        
        for pattern, description in patterns_to_check:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if len(matches) > 1:
                multi_indicators += 1
                
        # اگر 2 یا بیشتر الگو تکرار شده چندکالایی است
        is_multi = multi_indicators >= 2
        
        # بررسی تعداد صفحات (اگر متن طولانی باشد)
        if len(text) > 5000 and not is_multi:
            # احتمال چندکالایی بالا
            is_multi = True
            
        # تشخیص نهایی
        if is_import:
            return 'import_multi' if is_multi else 'import_single'
        else:
            return 'export_multi' if is_multi else 'export_single'
            
    def convert_pdf_to_images(self, pdf_path: str) -> List[str]:
        """تبدیل PDF به تصاویر - بهبود یافته"""
        
        images = []
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # باز کردن PDF
            pdf_document = fitz.open(pdf_path)
            
            self.logger.info(f"📄 تبدیل PDF با {len(pdf_document)} صفحه")
            
            for page_num in range(len(pdf_document)):
                try:
                    # تبدیل صفحه به تصویر
                    page = pdf_document[page_num]
                    
                    # تنظیمات کیفیت بالا
                    matrix = fitz.Matrix(self.config['dpi']/72, self.config['dpi']/72)
                    pix = page.get_pixmap(matrix=matrix, alpha=False)
                    
                    # ذخیره تصویر
                    img_path = temp_dir / f"{Path(pdf_path).stem}_page_{page_num}.png"
                    pix.save(str(img_path))
                    images.append(str(img_path))
                    
                    self.logger.info(f"✅ صفحه {page_num + 1} تبدیل شد")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ خطا در تبدیل صفحه {page_num}: {e}")
                    continue
                    
            pdf_document.close()
            
            self.logger.info(f"✅ {len(images)} تصویر ایجاد شد")
            return images
            
        except Exception as e:
            self.logger.error(f"❌ خطا در تبدیل PDF: {e}")
            return []
            
    def preprocess_image_advanced(self, image_path: str) -> tuple:
        """پیشپردازش پیشرفته تصویر"""
        
        try:
            # خواندن تصویر
            image = cv2.imread(image_path)
            if image is None:
                return None, None, None
                
            # تبدیل به grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # مجموعه تصاویر بهبود یافته
            processed_images = [gray]
            
            if self.config['enhance_image']:
                # روش 1: CLAHE
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                enhanced1 = clahe.apply(gray)
                processed_images.append(enhanced1)
                
                # روش 2: تنظیم کنتراست
                alpha = 1.5  # کنتراست
                beta = 30    # روشنایی
                enhanced2 = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
                processed_images.append(enhanced2)
                
                # روش 3: فیلتر گاوسی + کاهش نویز
                blurred = cv2.GaussianBlur(gray, (3, 3), 0)
                enhanced3 = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)
                processed_images.append(enhanced3)
                
                # روش 4: Morphological operations
                kernel = np.ones((2,2), np.uint8)
                enhanced4 = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
                processed_images.append(enhanced4)
                
            return processed_images
            
        except Exception as e:
            self.logger.warning(f"⚠️ خطا در پیشپردازش {image_path}: {e}")
            return [None]
            
    def extract_text_from_image_advanced(self, image_path: str) -> str:
        """استخراج متن پیشرفته از تصویر"""
        
        # بررسی کش
        if image_path in self.ocr_cache:
            return self.ocr_cache[image_path]
            
        try:
            # پیشپردازش
            processed_images = self.preprocess_image_advanced(image_path)
            
            if not processed_images or processed_images[0] is None:
                return ""
                
            all_text = ""
            best_text = ""
            max_length = 0
            
            # OCR روی همه نسخههای پردازش شده
            for i, img in enumerate(processed_images):
                if img is None:
                    continue
                    
                try:
                    # تنظیمات مختلف OCR
                    ocr_configs = [
                        {'detail': 0, 'paragraph': False, 'width_ths': 0.7, 'height_ths': 0.7},
                        {'detail': 0, 'paragraph': True, 'width_ths': 0.5, 'height_ths': 0.5},
                        {'detail': 0, 'paragraph': False, 'width_ths': 0.9, 'height_ths': 0.9}
                    ]
                    
                    for config in ocr_configs:
                        results = self.ocr_reader.readtext(img, **config)
                        
                        if results:
                            text = " ".join(results) if isinstance(results[0], str) else " ".join([r[1] for r in results])
                            
                            if len(text) > max_length:
                                max_length = len(text)
                                best_text = text
                                
                            all_text += " " + text
                            
                except Exception as e:
                    self.logger.warning(f"خطا در OCR نسخه {i}: {e}")
                    continue
                    
            # انتخاب بهترین نتیجه
            final_text = best_text if best_text else all_text
            
            # تبدیل اعداد فارسی/عربی به انگلیسی
            final_text = self.normalize_digits(final_text)
            
            # پاکسازی متن
            final_text = self.clean_text(final_text)
            
            # ذخیره در کش
            self.ocr_cache[image_path] = final_text
            
            return final_text
            
        except Exception as e:
            self.logger.warning(f"⚠️ خطا در OCR {image_path}: {e}")
            return ""
            
    def clean_text(self, text: str) -> str:
        """پاکسازی و بهبود متن"""
        
        if not text:
            return ""
            
        # حذف کاراکترهای غیرضروری
        text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFFa-zA-Z0-9\s\.\:\-\(\)]', ' ', text)
        
        # تنظیم فاصلهها
        text = re.sub(r'\s+', ' ', text)
        
        # حذف فاصلههای اضافی
        text = text.strip()
        
        return text
        
    def normalize_digits(self, text: str) -> str:
        """تبدیل اعداد فارسی و عربی به انگلیسی"""
        
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        arabic_digits = '٠١٢٣٤٥٦٧٨٩'
        english_digits = '0123456789'
        
        # تبدیل فارسی
        for p_digit, e_digit in zip(persian_digits, english_digits):
            text = text.replace(p_digit, e_digit)
            
        # تبدیل عربی
        for a_digit, e_digit in zip(arabic_digits, english_digits):
            text = text.replace(a_digit, e_digit)
            
        return text
        
    def extract_field_with_patterns_advanced(self, text: str, field_name: str, doc_type: str = 'import_single') -> Dict[str, Any]:
        """استخراج فیلد با الگوهای پیشرفته"""
        
        # انتخاب الگوهای مناسب
        if doc_type.startswith('import'):
            patterns_dict = self.import_patterns
        else:
            patterns_dict = self.export_patterns
            
        if field_name not in patterns_dict:
            return {'value': None, 'confidence': 0.0, 'method': 'none', 'pattern': None}
            
        field_config = patterns_dict[field_name]
        patterns = field_config['patterns']
        validator = field_config['validation']
        priority = field_config.get('priority', 5)
        
        # نتایج مختلف
        candidates = []
        
        # جستجو با الگوها
        for pattern_idx, pattern in enumerate(patterns):
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                
                for match in matches:
                    if match.groups():
                        candidate = match.group(1).strip()
                        
                        # پاکسازی بر اساس نوع فیلد
                        candidate = self.clean_field_value(candidate, field_name)
                        
                        # اعتبارسنجی
                        if candidate and validator(candidate):
                            # محاسبه امتیاز کیفیت
                            quality_score = self.calculate_quality_score(
                                candidate, pattern, pattern_idx, match, text
                            )
                            
                            candidates.append({
                                'value': candidate,
                                'confidence': quality_score,
                                'method': 'regex',
                                'pattern': pattern,
                                'priority': priority,
                                'position': match.start()
                            })
                            
            except Exception as e:
                self.logger.warning(f"خطا در الگو {pattern}: {e}")
                continue
                
        # انتخاب بهترین نامزد
        if candidates:
            # مرتبسازی بر اساس اولویت و کیفیت
            candidates.sort(key=lambda x: (x['priority'], -x['confidence'], x['position']))
            best_candidate = candidates[0]
            
            return {
                'value': best_candidate['value'],
                'confidence': min(best_candidate['confidence'], 0.95),  # حداکثر 95%
                'method': best_candidate['method'],
                'pattern': best_candidate['pattern']
            }
            
        return {'value': None, 'confidence': 0.0, 'method': 'none', 'pattern': None}
        
    def clean_field_value(self, value: str, field_name: str) -> str:
        """پاکسازی مقدار فیلد بر اساس نوع"""
        
        if not value:
            return ""
            
        # پاکسازی عمومی
        value = value.strip()
        
        # پاکسازی خاص هر فیلد
        if field_name in ['شماره_کوتا', 'کد_کالا', 'تعداد_بسته']:
            # فقط اعداد
            value = re.sub(r'[^\d]', '', value)
            
        elif field_name in ['وزن_خالص', 'نرخ_ارز', 'ارزش_گمرکی', 'بیمه', 'کرایه']:
            # اعداد و اعشار
            value = re.sub(r'[^\d\.]', '', value)
            # حذف نقطههای اضافی
            parts = value.split('.')
            if len(parts) > 2:
                value = parts[0] + '.' + ''.join(parts[1:])
                
        elif field_name in ['شرح_کالا', 'نوع_بسته', 'کشور_طرف_معامله']:
            # متن - حذف اعداد و کاراکترهای خاص
            value = re.sub(r'\d+', '', value)
            value = re.sub(r'[^\u0600-\u06FFa-zA-Z\s]', ' ', value)
            value = re.sub(r'\s+', ' ', value).strip()
            
        elif field_name == 'نوع_ارز':
            # حروف بزرگ انگلیسی
            value = re.sub(r'[^A-Z]', '', value.upper())
            
        return value
        
    def calculate_quality_score(self, candidate: str, pattern: str, pattern_idx: int, match, full_text: str) -> float:
        """محاسبه امتیاز کیفیت نامزد"""
        
        score = 0.5  # امتیاز پایه
        
        # امتیاز بر اساس اولویت الگو
        score += (10 - pattern_idx) * 0.05
        
        # امتیاز بر اساس طول مناسب
        if 5 <= len(candidate) <= 20:
            score += 0.1
        elif len(candidate) > 20:
            score -= 0.1
            
        # امتیاز بر اساس موقعیت در متن
        position_ratio = match.start() / len(full_text)
        if position_ratio < 0.5:  # در نیمه اول متن
            score += 0.1
            
        # امتیاز بر اساس کلمات کلیدی اطراف
        context = full_text[max(0, match.start()-50):match.end()+50]
        
        # کلمات مثبت
        positive_keywords = ['کوتا', 'کالا', 'شرح', 'وزن', 'کشور', 'ارز', 'گمرک']
        for keyword in positive_keywords:
            if keyword in context:
                score += 0.05
                
        # کلمات منفی
        negative_keywords = ['تاریخ', 'ساعت', 'شماره تلفن', 'کد پستی']
        for keyword in negative_keywords:
            if keyword in context:
                score -= 0.1
                
        # حداکثر و حداقل امتیاز
        score = max(0.1, min(score, 0.9))
        
        return score
        
    def extract_from_single_page_advanced(self, image_path: str, page_num: int = 0) -> Dict[str, Any]:
        """استخراج پیشرفته از یک صفحه"""
        
        start_time = time.time()
        
        try:
            # استخراج متن
            text = self.extract_text_from_image_advanced(image_path)
            
            if not text:
                return self._empty_page_result(image_path, page_num)
                
            # تشخیص نوع سند
            doc_type = self.detect_document_type(text)
            
            # انتخاب فیلدها بر اساس نوع سند و صفحه
            if page_num == 0:
                # صفحه اول - همه فیلدها
                fields_to_extract = list(self.import_patterns.keys())
            else:
                # صفحات بعدی - فیلدهای کالا
                fields_to_extract = [
                    'شرح_کالا', 'تعداد_بسته', 'نوع_بسته', 'وزن_خالص',
                    'کد_کالا', 'بیمه', 'کرایه', 'تعداد_واحد_کالا',
                    'ارزش_قلم_کالا', 'ارزش_گمرکی', 'مبلغ_حقوق_ورودی',
                    'مالیات_بر_ارزش_افزوده', 'جمع_حقوق_عوارض'
                ]
                
            # استخراج فیلدها
            extracted_data = {}
            
            for field_name in fields_to_extract:
                result = self.extract_field_with_patterns_advanced(text, field_name, doc_type)
                extracted_data[field_name] = result
                
            processing_time = time.time() - start_time
            
            # محاسبه آمار
            successful_fields = sum(1 for field in extracted_data.values() if field['value'])
            success_rate = (successful_fields / len(fields_to_extract)) * 100 if fields_to_extract else 0
            
            return {
                'file': Path(image_path).name,
                'page': page_num,
                'document_type': doc_type,
                'extracted': extracted_data,
                'text_length': len(text),
                'full_text': text,
                'processing_time': f"{processing_time:.1f}s",
                'success_rate': f"{success_rate:.1f}%",
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطا در استخراج {image_path}: {e}")
            return self._empty_page_result(image_path, page_num)
            
    def _empty_page_result(self, image_path: str, page_num: int) -> Dict[str, Any]:
        """نتیجه خالی برای صفحه"""
        return {
            'file': Path(image_path).name,
            'page': page_num,
            'document_type': 'unknown',
            'extracted': {field: {'value': None, 'confidence': 0.0, 'method': 'none', 'pattern': None} 
                         for field in self.import_patterns.keys()},
            'text_length': 0,
            'full_text': '',
            'processing_time': '0s',
            'success_rate': '0%',
            'status': 'failed'
        }
        
    def process_single_file(self, file_path: str) -> Dict[str, Any]:
        """پردازش یک فایل"""
        
        self.logger.info(f"🔄 پردازش {file_path}")
        
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.pdf':
                # تبدیل PDF به تصاویر
                image_paths = self.convert_pdf_to_images(file_path)
                
                if not image_paths:
                    return {
                        'type': 'pdf',
                        'pages': [self._empty_page_result(file_path, 0)],
                        'total_pages': 0,
                        'status': 'failed'
                    }
                
                # پردازش هر صفحه
                document_results = []
                
                for i, img_path in enumerate(image_paths):
                    result = self.extract_from_single_page_advanced(img_path, i)
                    document_results.append(result)
                    
                return {
                    'type': 'pdf',
                    'pages': document_results,
                    'total_pages': len(image_paths),
                    'status': 'success'
                }
                
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                # پردازش تصویر منفرد
                result = self.extract_from_single_page_advanced(file_path, 0)
                
                return {
                    'type': 'image',
                    'pages': [result],
                    'total_pages': 1,
                    'status': 'success' if result['status'] == 'success' else 'failed'
                }
                
            else:
                raise ValueError(f"نوع فایل پشتیبانی نمیشود: {file_ext}")
                
        except Exception as e:
            self.logger.error(f"❌ خطا در پردازش {file_path}: {e}")
            return {
                'type': 'unknown',
                'pages': [self._empty_page_result(file_path, 0)],
                'total_pages': 0,
                'status': 'failed',
                'error': str(e)
            }
            
    def process_files(self, files: List[str]) -> Dict[str, Any]:
        """پردازش لیست فایلها"""
        
        all_results = {}
        
        for file_path in files:
            result = self.process_single_file(file_path)
            all_results[file_path] = result
            
        return all_results
        
    def get_extraction_stats(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """محاسبه آمار استخراج - بهبود یافته"""
        
        stats = {
            'total_files': len(results),
            'total_pages': 0,
            'successful_extractions': {},
            'processing_time': 0.0,
            'document_types': {},
            'average_confidence': 0.0,
            'field_analysis': {}
        }
        
        # آمار تفصیلی
        field_stats = {}
        all_confidences = []
        
        for file_path, file_result in results.items():
            if 'pages' not in file_result:
                continue
                
            stats['total_pages'] += file_result.get('total_pages', 0)
            
            for page_result in file_result['pages']:
                # نوع سند
                doc_type = page_result.get('document_type', 'unknown')
                stats['document_types'][doc_type] = stats['document_types'].get(doc_type, 0) + 1
                
                # زمان پردازش
                time_str = page_result.get('processing_time', '0s')
                try:
                    time_val = float(time_str.replace('s', ''))
                    stats['processing_time'] += time_val
                except:
                    pass
                    
                # فیلدهای استخراج شده
                for field_name, field_data in page_result.get('extracted', {}).items():
                    if field_name not in field_stats:
                        field_stats[field_name] = {
                            'total': 0, 
                            'successful': 0, 
                            'confidences': [],
                            'methods': {}
                        }
                        
                    field_stats[field_name]['total'] += 1
                    
                    if field_data.get('value'):
                        field_stats[field_name]['successful'] += 1
                        confidence = field_data.get('confidence', 0.0)
                        field_stats[field_name]['confidences'].append(confidence)
                        all_confidences.append(confidence)
                        
                        method = field_data.get('method', 'unknown')
                        field_stats[field_name]['methods'][method] = \
                            field_stats[field_name]['methods'].get(method, 0) + 1
                            
        # محاسبه درصد موفقیت و آمار تفصیلی
        for field_name, field_data in field_stats.items():
            if field_data['total'] > 0:
                success_rate = (field_data['successful'] / field_data['total']) * 100
                avg_confidence = sum(field_data['confidences']) / len(field_data['confidences']) \
                    if field_data['confidences'] else 0
                    
                stats['successful_extractions'][field_name] = {
                    'count': f"{field_data['successful']}/{field_data['total']}",
                    'percentage': f"{success_rate:.1f}%",
                    'avg_confidence': f"{avg_confidence:.2f}",
                    'methods': field_data['methods']
                }
                
                stats['field_analysis'][field_name] = {
                    'success_rate': success_rate,
                    'confidence': avg_confidence,
                    'total_attempts': field_data['total'],
                    'successful_attempts': field_data['successful']
                }
                
        # میانگین اطمینان کلی
        stats['average_confidence'] = sum(all_confidences) / len(all_confidences) \
            if all_confidences else 0.0
            
        return stats
        
    def update_config(self, new_config: Dict[str, Any]):
        """بهروزرسانی تنظیمات"""
        self.config.update(new_config)
        
        # بازسازی OCR در صورت تغییر زبانها
        if 'languages' in new_config:
            self.setup_ocr()
            
        # پاک کردن کش
        self.ocr_cache.clear()
        
    def get_supported_fields(self) -> List[str]:
        """دریافت لیست فیلدهای پشتیبانی شده"""
        return list(self.import_patterns.keys())
        
    def validate_pattern(self, pattern: str) -> bool:
        """اعتبارسنجی الگوی regex"""
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False
