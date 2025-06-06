#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 سیستم یادگیری هوشمند اسناد گمرکی
توسعهدهنده: Mohsen-data-wizard
تاریخ: 2025-06-05
"""

import json
import re
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import pickle
import hashlib

class LearningSystem:
    def __init__(self):
        """سیستم یادگیری هوشمند"""
        
        # تنظیم logging
        self.logger = logging.getLogger(__name__)
        
        # مسیرهای ذخیره
        self.patterns_dir = Path("patterns")
        self.patterns_dir.mkdir(exist_ok=True)
        
        self.learned_patterns_file = self.patterns_dir / "learned_patterns.json"
        self.user_corrections_file = self.patterns_dir / "user_corrections.json"
        self.performance_log_file = self.patterns_dir / "performance_log.json"
        
        # ساختار دادههای یادگیری
        self.learned_patterns = {}
        self.user_corrections = []
        self.performance_log = []
        
        # آمار یادگیری
        self.learning_stats = {
            'total_corrections': 0,
            'successful_patterns': 0,
            'accuracy_improvement': 0.0,
            'last_learning_session': None
        }
        
        # بارگذاری دادههای موجود
        self.load_all_data()
        
    def load_all_data(self):
        """بارگذاری تمام دادههای یادگیری"""
        try:
            self.load_patterns()
            self.load_corrections()
            self.load_performance_log()
            self.logger.info("✅ دادههای یادگیری بارگذاری شد")
        except Exception as e:
            self.logger.warning(f"⚠️ خطا در بارگذاری دادهها: {e}")
            
    def load_patterns(self):
        """بارگذاری الگوهای یاد گرفته شده"""
        try:
            if self.learned_patterns_file.exists():
                with open(self.learned_patterns_file, 'r', encoding='utf-8') as f:
                    self.learned_patterns = json.load(f)
                self.logger.info(f"📚 {len(self.learned_patterns)} الگو بارگذاری شد")
            else:
                self.learned_patterns = {}
        except Exception as e:
            self.logger.error(f"❌ خطا در بارگذاری الگوها: {e}")
            self.learned_patterns = {}
            
    def load_corrections(self):
        """بارگذاری تصحیحات کاربر"""
        try:
            if self.user_corrections_file.exists():
                with open(self.user_corrections_file, 'r', encoding='utf-8') as f:
                    self.user_corrections = json.load(f)
                self.learning_stats['total_corrections'] = len(self.user_corrections)
        except Exception as e:
            self.logger.error(f"❌ خطا در بارگذاری تصحیحات: {e}")
            self.user_corrections = []
            
    def load_performance_log(self):
        """بارگذاری لاگ عملکرد"""
        try:
            if self.performance_log_file.exists():
                with open(self.performance_log_file, 'r', encoding='utf-8') as f:
                    self.performance_log = json.load(f)
        except Exception as e:
            self.logger.error(f"❌ خطا در بارگذاری لاگ عملکرد: {e}")
            self.performance_log = []
            
    def learn_from_edits(self, edit_widgets: Dict[str, Any]):
        """یادگیری از ویرایشهای کاربر"""
        
        learning_session = {
            'session_id': self.generate_session_id(),
            'timestamp': datetime.now().isoformat(),
            'user': 'Mohsen-data-wizard',
            'corrections': [],
            'new_patterns': [],
            'improved_patterns': []
        }
        
        try:
            for field_id, widget_data in edit_widgets.items():
                current_value = widget_data['var'].get().strip()
                original_value = widget_data['original_value']
                field_name = widget_data['label']
                confidence = widget_data['confidence']
                method = widget_data['method']
                
                # بررسی تغییر
                if current_value != original_value:
                    correction = self.process_correction(
                        field_id, field_name, original_value, 
                        current_value, confidence, method
                    )
                    
                    if correction:
                        learning_session['corrections'].append(correction)
                        self.user_corrections.append(correction)
                        
                        # تولید الگوی جدید
                        new_pattern = self.generate_pattern_from_correction(correction)
                        if new_pattern:
                            learning_session['new_patterns'].append(new_pattern)
                            self.add_learned_pattern(field_name, new_pattern)
                            
            # ذخیره جلسه یادگیری
            if learning_session['corrections']:
                self.performance_log.append(learning_session)
                self.learning_stats['last_learning_session'] = learning_session['session_id']
                self.learning_stats['total_corrections'] += len(learning_session['corrections'])
                
                # ذخیره تغییرات
                self.save_all_data()
                
                self.logger.info(f"🎓 یادگیری کامل شد: {len(learning_session['corrections'])} تصحیح")
                return True
            else:
                self.logger.info("ℹ️ تغییری برای یادگیری یافت نشد")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ خطا در یادگیری: {e}")
            return False
            
    def process_correction(self, field_id: str, field_name: str, original: str, 
                          corrected: str, confidence: float, method: str) -> Optional[Dict]:
        """پردازش یک تصحیح"""
        
        try:
            correction = {
                'correction_id': self.generate_correction_id(field_id, original, corrected),
                'field_id': field_id,
                'field_name': field_name,
                'original_value': original,
                'corrected_value': corrected,
                'original_confidence': confidence,
                'extraction_method': method,
                'timestamp': datetime.now().isoformat(),
                'user': 'Mohsen-data-wizard',
                'correction_type': self.classify_correction(original, corrected),
                'quality_score': self.calculate_correction_quality(original, corrected)
            }
            
            return correction
            
        except Exception as e:
            self.logger.error(f"خطا در پردازش تصحیح: {e}")
            return None
            
    def classify_correction(self, original: str, corrected: str) -> str:
        """طبقهبندی نوع تصحیح"""
        
        if not original and corrected:
            return "addition"  # اضافه کردن مقدار جدید
        elif original and not corrected:
            return "deletion"  # حذف مقدار نادرست
        elif original and corrected:
            if self.are_similar_values(original, corrected):
                return "refinement"  # بهبود و تصحیح جزئی
            else:
                return "replacement"  # جایگزینی کامل
        else:
            return "unknown"
            
    def are_similar_values(self, val1: str, val2: str, threshold: float = 0.7) -> bool:
        """بررسی شباهت دو مقدار"""
        
        if not val1 or not val2:
            return False
            
        # تبدیل به حروف کوچک و حذف فاصلهها
        val1_clean = re.sub(r'\s+', '', val1.lower())
        val2_clean = re.sub(r'\s+', '', val2.lower())
        
        # محاسبه شباهت
        if val1_clean == val2_clean:
            return True
            
        # بررسی شامل بودن
        if val1_clean in val2_clean or val2_clean in val1_clean:
            return True
            
        # محاسبه شباهت کاراکتری
        similarity = self.calculate_string_similarity(val1_clean, val2_clean)
        return similarity >= threshold
        
    def calculate_string_similarity(self, str1: str, str2: str) -> float:
        """محاسبه شباهت دو رشته"""
        
        if not str1 or not str2:
            return 0.0
            
        # الگوریتم Levenshtein ساده
        len1, len2 = len(str1), len(str2)
        
        if len1 == 0:
            return 0.0 if len2 > 0 else 1.0
        if len2 == 0:
            return 0.0
            
        # ماتریس فاصله
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
            
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if str1[i-1] == str2[j-1]:
                    cost = 0
                else:
                    cost = 1
                    
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # حذف
                    matrix[i][j-1] + 1,      # اضافه
                    matrix[i-1][j-1] + cost  # جایگزینی
                )
                
        # تبدیل فاصله به شباهت
        max_len = max(len1, len2)
        distance = matrix[len1][len2]
        similarity = 1.0 - (distance / max_len)
        
        return similarity
        
    def calculate_correction_quality(self, original: str, corrected: str) -> float:
        """محاسبه کیفیت تصحیح"""
        
        quality = 0.5  # امتیاز پایه
        
        # امتیاز بر اساس طول مناسب
        if corrected and 3 <= len(corrected) <= 50:
            quality += 0.2
            
        # امتیاز بر اساس نوع تصحیح
        correction_type = self.classify_correction(original, corrected)
        
        if correction_type == "addition" and corrected:
            quality += 0.3  # اضافه کردن مقدار جدید ارزشمند است
        elif correction_type == "refinement":
            quality += 0.2  # بهبود جزئی
        elif correction_type == "replacement":
            quality += 0.1  # جایگزینی کامل
            
        # امتیاز بر اساس محتوا
        if corrected:
            # بررسی الگوهای عددی
            if re.search(r'\d+', corrected):
                quality += 0.1
                
            # بررسی کلمات فارسی
            if re.search(r'[\u0600-\u06FF]+', corrected):
                quality += 0.1
                
        # محدود کردن امتیاز
        return max(0.1, min(quality, 1.0))
        
    def generate_pattern_from_correction(self, correction: Dict) -> Optional[Dict]:
        """تولید الگوی جدید از روی تصحیح"""
        
        try:
            field_name = correction['field_name']
            corrected_value = correction['corrected_value']
            correction_type = correction['correction_type']
            
            if not corrected_value or correction_type == "deletion":
                return None
                
            # تولید الگوی regex بر اساس مقدار تصحیح شده
            patterns = []
            
            # الگوهای عددی
            if re.match(r'^\d+$', corrected_value):
                # عدد خالص
                patterns.extend([
                    f"({re.escape(corrected_value)})",
                    f"[\s:]({re.escape(corrected_value)})[\s\n]",
                    f"{re.escape(corrected_value)}\s*[^\d]"
                ])
                
            elif re.match(r'^\d+\.\d+$', corrected_value):
                # عدد اعشاری
                base_num = corrected_value.split('.')[0]
                patterns.extend([
                    f"({re.escape(corrected_value)})",
                    f"{re.escape(base_num)}\.?\d*",
                    f"[\s:]({re.escape(corrected_value)})[\s\n]"
                ])
                
            # الگوهای متنی
            elif re.match(r'^[آ-ی\s]+$', corrected_value):
                # متن فارسی
                words = corrected_value.split()
                if len(words) == 1:
                    patterns.extend([
                        f"({re.escape(corrected_value)})",
                        f"[\s:]({re.escape(corrected_value)})[\s\n]",
                        f"({corrected_value})\s*\d"
                    ])
                else:
                    # چند کلمه
                    patterns.extend([
                        f"({re.escape(corrected_value)})",
                        f"[\s:]({re.escape(corrected_value)})[\s\n]"
                    ])
                    
            # الگوهای ترکیبی
            elif re.match(r'^[A-Z]{2,4}$', corrected_value):
                # کد ارز
                patterns.extend([
                    f"({re.escape(corrected_value)})",
                    f"[\s:]({re.escape(corrected_value)})[\s\n]",
                    f"ارز[\s:]*({re.escape(corrected_value)})"
                ])
                
            else:
                # الگوی عمومی
                patterns.append(f"({re.escape(corrected_value)})")
                
            # انتخاب بهترین الگو
            if patterns:
                best_pattern = self.select_best_pattern(patterns, field_name)
                
                return {
                    'pattern': best_pattern,
                    'field_name': field_name,
                    'source_value': corrected_value,
                    'correction_id': correction['correction_id'],
                    'created_at': datetime.now().isoformat(),
                    'success_count': 1,
                    'total_attempts': 1,
                    'accuracy': 100.0,
                    'quality_score': correction['quality_score'],
                    'pattern_type': 'user_generated'
                }
                
        except Exception as e:
            self.logger.error(f"خطا در تولید الگو: {e}")
            
        return None
        
    def select_best_pattern(self, patterns: List[str], field_name: str) -> str:
        """انتخاب بهترین الگو از لیست"""
        
        # امتیازدهی الگوها
        pattern_scores = []
        
        for pattern in patterns:
            score = 0.5  # امتیاز پایه
            
            # الگوهای دقیقتر امتیاز بیشتر
            if r'\s' in pattern:
                score += 0.2
            if r'[\s:]' in pattern:
                score += 0.3
            if len(pattern) > 20:
                score += 0.1
                
            # الگوهای خاص فیلد
            if field_name == 'شماره_کوتا' and r'\d' in pattern:
                score += 0.2
            elif field_name == 'شرح_کالا' and 'آ-ی' in pattern:
                score += 0.2
                
            pattern_scores.append((pattern, score))
            
        # مرتبسازی و انتخاب بهترین
        pattern_scores.sort(key=lambda x: x[1], reverse=True)
        
        return pattern_scores[0][0] if pattern_scores else patterns[0]
        
    def add_learned_pattern(self, field_name: str, pattern_data: Dict):
        """اضافه کردن الگوی یاد گرفته شده"""
        
        try:
            if field_name not in self.learned_patterns:
                self.learned_patterns[field_name] = []
                
            # بررسی تکراری نبودن
            existing_patterns = [p['pattern'] for p in self.learned_patterns[field_name]]
            
            if pattern_data['pattern'] not in existing_patterns:
                self.learned_patterns[field_name].append(pattern_data)
                self.learning_stats['successful_patterns'] += 1
                
                self.logger.info(f"✅ الگوی جدید برای {field_name} اضافه شد")
                return True
            else:
                # بهروزرسانی الگوی موجود
                for i, existing_pattern in enumerate(self.learned_patterns[field_name]):
                    if existing_pattern['pattern'] == pattern_data['pattern']:
                        existing_pattern['success_count'] += 1
                        existing_pattern['total_attempts'] += 1
                        existing_pattern['accuracy'] = (
                            existing_pattern['success_count'] / 
                            existing_pattern['total_attempts'] * 100
                        )
                        break
                        
                return True
                
        except Exception as e:
            self.logger.error(f"خطا در اضافه کردن الگو: {e}")
            return False
            
    def get_learned_patterns(self) -> Dict[str, List[Dict]]:
        """دریافت الگوهای یاد گرفته شده"""
        return self.learned_patterns.copy()
        
    def add_custom_pattern(self, field_name: str, pattern: str) -> bool:
        """اضافه کردن الگوی دستی"""
        
        try:
            # اعتبارسنجی الگو
            re.compile(pattern)
            
            custom_pattern = {
                'pattern': pattern,
                'field_name': field_name,
                'source_value': 'دستی',
                'correction_id': f"manual_{datetime.now().timestamp()}",
                'created_at': datetime.now().isoformat(),
                'success_count': 0,
                'total_attempts': 0,
                'accuracy': 0.0,
                'quality_score': 0.5,
                'pattern_type': 'manual'
            }
            
            return self.add_learned_pattern(field_name, custom_pattern)
            
        except re.error as e:
            self.logger.error(f"الگوی نامعتبر: {e}")
            return False
        except Exception as e:
            self.logger.error(f"خطا در اضافه کردن الگوی دستی: {e}")
            return False
            
    def remove_pattern(self, field_name: str, pattern: str) -> bool:
        """حذف الگو"""
        
        try:
            if field_name in self.learned_patterns:
                original_count = len(self.learned_patterns[field_name])
                
                self.learned_patterns[field_name] = [
                    p for p in self.learned_patterns[field_name] 
                    if p['pattern'] != pattern
                ]
                
                removed_count = original_count - len(self.learned_patterns[field_name])
                
                if removed_count > 0:
                    self.logger.info(f"🗑️ {removed_count} الگو حذف شد")
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"خطا در حذف الگو: {e}")
            return False
            
    def update_pattern_performance(self, field_name: str, pattern: str, success: bool):
        """بهروزرسانی عملکرد الگو"""
        
        try:
            if field_name in self.learned_patterns:
                for pattern_data in self.learned_patterns[field_name]:
                    if pattern_data['pattern'] == pattern:
                        pattern_data['total_attempts'] += 1
                        
                        if success:
                            pattern_data['success_count'] += 1
                            
                        # محاسبه مجدد دقت
                        if pattern_data['total_attempts'] > 0:
                            pattern_data['accuracy'] = (
                                pattern_data['success_count'] / 
                                pattern_data['total_attempts'] * 100
                            )
                            
                        break
                        
        except Exception as e:
            self.logger.error(f"خطا در بهروزرسانی عملکرد: {e}")
            
    def get_best_patterns_for_field(self, field_name: str, min_accuracy: float = 70.0) -> List[Dict]:
        """دریافت بهترین الگوها برای یک فیلد"""
        
        if field_name not in self.learned_patterns:
            return []
            
        # فیلتر و مرتبسازی
        good_patterns = [
            p for p in self.learned_patterns[field_name]
            if p['accuracy'] >= min_accuracy and p['total_attempts'] >= 2
        ]
        
        # مرتبسازی بر اساس دقت و تعداد موفقیت
        good_patterns.sort(
            key=lambda x: (x['accuracy'], x['success_count']), 
            reverse=True
        )
        
        return good_patterns[:5]  # 5 الگوی برتر
        
    def analyze_learning_progress(self) -> Dict[str, Any]:
        """تحلیل پیشرفت یادگیری"""
        
        analysis = {
            'total_patterns': sum(len(patterns) for patterns in self.learned_patterns.values()),
            'fields_with_patterns': len(self.learned_patterns),
            'total_corrections': len(self.user_corrections),
            'learning_sessions': len(self.performance_log),
            'field_analysis': {},
            'recent_activity': [],
            'improvement_suggestions': []
        }
        
        # تحلیل هر فیلد
        for field_name, patterns in self.learned_patterns.items():
            if patterns:
                accuracies = [p['accuracy'] for p in patterns if p['total_attempts'] > 0]
                
                analysis['field_analysis'][field_name] = {
                    'pattern_count': len(patterns),
                    'avg_accuracy': sum(accuracies) / len(accuracies) if accuracies else 0,
                    'best_accuracy': max(accuracies) if accuracies else 0,
                    'total_attempts': sum(p['total_attempts'] for p in patterns),
                    'successful_attempts': sum(p['success_count'] for p in patterns)
                }
                
        # فعالیتهای اخیر
        recent_corrections = sorted(
            self.user_corrections, 
            key=lambda x: x['timestamp'], 
            reverse=True
        )[:10]
        
        analysis['recent_activity'] = recent_corrections
        
        # پیشنهادات بهبود
        suggestions = []
        
        for field_name, field_stats in analysis['field_analysis'].items():
            if field_stats['avg_accuracy'] < 50:
                suggestions.append(f"فیلد {field_name} نیاز به الگوهای بیشتر دارد")
            elif field_stats['pattern_count'] > 10:
                suggestions.append(f"فیلد {field_name} دارای الگوهای زیادی است - ممکن است نیاز به پاکسازی داشته باشد")
                
        analysis['improvement_suggestions'] = suggestions
        
        return analysis
        
    def export_patterns_for_sharing(self, output_file: str) -> bool:
        """خروجی الگوها برای اشتراک"""
        
        try:
            export_data = {
                'export_info': {
                    'created_by': 'Mohsen-data-wizard',
                    'created_at': datetime.now().isoformat(),
                    'version': '2.0',
                    'total_patterns': sum(len(p) for p in self.learned_patterns.values())
                },
                'patterns': {},
                'statistics': self.learning_stats
            }
            
            # صرفا الگوهای موفق
            for field_name, patterns in self.learned_patterns.items():
                successful_patterns = [
                    p for p in patterns 
                    if p['accuracy'] >= 60 and p['total_attempts'] >= 3
                ]
                
                if successful_patterns:
                    export_data['patterns'][field_name] = successful_patterns
                    
            # ذخیره
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"📤 الگوها به {output_file} صادر شد")
            return True
            
        except Exception as e:
            self.logger.error(f"خطا در صادر کردن: {e}")
            return False
            
    def import_patterns_from_file(self, input_file: str) -> bool:
        """وارد کردن الگوها از فایل"""
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
                
            if 'patterns' not in import_data:
                raise ValueError("فرمت فایل نامعتبر است")
                
            imported_count = 0
            
            for field_name, patterns in import_data['patterns'].items():
                for pattern_data in patterns:
                    # اضافه کردن با علامتگذاری ورودی
                    pattern_data['pattern_type'] = 'imported'
                    pattern_data['imported_at'] = datetime.now().isoformat()
                    
                    if self.add_learned_pattern(field_name, pattern_data):
                        imported_count += 1
                        
            self.logger.info(f"📥 {imported_count} الگو وارد شد")
            return True
            
        except Exception as e:
            self.logger.error(f"خطا در وارد کردن: {e}")
            return False
            
    def save_all_data(self):
        """ذخیره تمام دادههای یادگیری"""
        try:
            self.save_patterns()
            self.save_corrections()
            self.save_performance_log()
        except Exception as e:
            self.logger.error(f"خطا در ذخیره دادهها: {e}")
            
    def save_patterns(self):
        """ذخیره الگوهای یاد گرفته شده"""
        try:
            with open(self.learned_patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.learned_patterns, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"خطا در ذخیره الگوها: {e}")
            
    def save_corrections(self):
        """ذخیره تصحیحات کاربر"""
        try:
            with open(self.user_corrections_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_corrections, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"خطا در ذخیره تصحیحات: {e}")
            
    def save_performance_log(self):
        """ذخیره لاگ عملکرد"""
        try:
            with open(self.performance_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.performance_log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"خطا در ذخیره لاگ عملکرد: {e}")
            
    def generate_session_id(self) -> str:
        """تولید شناسه جلسه یادگیری"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"learning_session_{timestamp}"
        
    def generate_correction_id(self, field_id: str, original: str, corrected: str) -> str:
        """تولید شناسه تصحیح"""
        content = f"{field_id}_{original}_{corrected}_{datetime.now().timestamp()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
        
    def get_learning_statistics(self) -> Dict[str, Any]:
        """دریافت آمار یادگیری"""
        
        stats = self.learning_stats.copy()
        
        # محاسبه آمار فعلی
        total_patterns = sum(len(patterns) for patterns in self.learned_patterns.values())
        successful_patterns = sum(
            1 for patterns in self.learned_patterns.values()
            for pattern in patterns
            if pattern['accuracy'] >= 70
        )
        
        stats.update({
            'current_total_patterns': total_patterns,
            'current_successful_patterns': successful_patterns,
            'success_rate': (successful_patterns / total_patterns * 100) if total_patterns > 0 else 0,
            'fields_count': len(self.learned_patterns),
            'last_update': datetime.now().isoformat()
        })
        
        return stats
        
    def cleanup_old_patterns(self, days_old: int = 30, min_accuracy: float = 30.0):
        """پاکسازی الگوهای قدیمی و ضعیف"""
        
        try:
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            cleaned_count = 0
            
            for field_name in list(self.learned_patterns.keys()):
                original_count = len(self.learned_patterns[field_name])
                
                # فیلتر الگوهای خوب
                self.learned_patterns[field_name] = [
                    pattern for pattern in self.learned_patterns[field_name]
                    if (
                        pattern['accuracy'] >= min_accuracy or
                        datetime.fromisoformat(pattern['created_at']).timestamp() > cutoff_date or
                        pattern.get('pattern_type') == 'manual'
                    )
                ]
                
                cleaned_count += original_count - len(self.learned_patterns[field_name])
                
                # حذف فیلدهای خالی
                if not self.learned_patterns[field_name]:
                    del self.learned_patterns[field_name]
                    
            if cleaned_count > 0:
                self.save_patterns()
                self.logger.info(f"🧹 {cleaned_count} الگوی قدیمی پاک شد")
                
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"خطا در پاکسازی: {e}")
            return 0
            
    def reset_learning_data(self, confirm: bool = False) -> bool:
        """بازنشانی کامل دادههای یادگیری"""
        
        if not confirm:
            return False
            
        try:
            self.learned_patterns = {}
            self.user_corrections = []
            self.performance_log = []
            self.learning_stats = {
                'total_corrections': 0,
                'successful_patterns': 0,
                'accuracy_improvement': 0.0,
                'last_learning_session': None
            }
            
            self.save_all_data()
            self.logger.info("🔄 دادههای یادگیری بازنشانی شد")
            return True
            
        except Exception as e:
            self.logger.error(f"خطا در بازنشانی: {e}")
            return False
            
    def validate_learned_patterns(self) -> Dict[str, List[str]]:
        """اعتبارسنجی الگوهای یاد گرفته شده"""
        
        validation_report = {
            'valid_patterns': [],
            'invalid_patterns': [],
            'warnings': []
        }
        
        try:
            for field_name, patterns in self.learned_patterns.items():
                for pattern_data in patterns:
                    pattern = pattern_data['pattern']
                    
                    try:
                        # تست کامپایل regex
                        re.compile(pattern)
                        validation_report['valid_patterns'].append(f"{field_name}: {pattern}")
                        
                        # هشدارها
                        if pattern_data['total_attempts'] == 0:
                            validation_report['warnings'].append(f"الگو استفاده نشده: {field_name}")
                        elif pattern_data['accuracy'] < 50:
                            validation_report['warnings'].append(f"الگوی ضعیف: {field_name} ({pattern_data['accuracy']:.1f}%)")
                            
                    except re.error:
                        validation_report['invalid_patterns'].append(f"{field_name}: {pattern}")
                        
        except Exception as e:
            self.logger.error(f"خطا در اعتبارسنجی: {e}")
            
        return validation_report
