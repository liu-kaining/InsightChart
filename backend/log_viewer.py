#!/usr/bin/env python3
"""
日志查看和分析工具

提供命令行方式查看和分析应用日志:
- 实时查看日志
- 按级别过滤日志
- 搜索特定内容
- 统计错误日志
- 导出日志报告
"""

import os
import json
import argparse
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path


class LogAnalyzer:
    """日志分析器"""
    
    def __init__(self, log_dir: str = './logs'):
        """
        初始化日志分析器
        
        Args:
            log_dir: 日志目录路径
        """
        self.log_dir = Path(log_dir)
        self.app_log_file = self.log_dir / 'app.log'
        self.error_log_file = self.log_dir / 'error.log'
    
    def tail_logs(self, lines: int = 50, follow: bool = False, level: Optional[str] = None):
        """
        查看日志尾部
        
        Args:
            lines: 显示行数
            follow: 是否实时跟踪
            level: 过滤日志级别
        """
        log_file = self.app_log_file
        
        if not log_file.exists():
            print(f"日志文件不存在: {log_file}")
            return
        
        if follow:
            self._follow_logs(log_file, level)
        else:
            self._show_tail_logs(log_file, lines, level)
    
    def _show_tail_logs(self, log_file: Path, lines: int, level: Optional[str]):
        """显示日志尾部内容"""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                
            # 过滤日志级别
            if level:
                filtered_lines = []
                for line in all_lines[-lines*3:]:  # 读取更多行以便过滤
                    if self._match_level(line, level):
                        filtered_lines.append(line)
                all_lines = filtered_lines
            
            # 显示最后N行
            for line in all_lines[-lines:]:
                print(self._format_log_line(line.strip()))
                
        except Exception as e:
            print(f"读取日志文件失败: {e}")
    
    def _follow_logs(self, log_file: Path, level: Optional[str]):
        """实时跟踪日志"""
        import time
        
        print(f"实时跟踪日志文件: {log_file}")
        print("按 Ctrl+C 退出")
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                # 移动到文件末尾
                f.seek(0, 2)
                
                while True:
                    line = f.readline()
                    if line:
                        if not level or self._match_level(line, level):
                            print(self._format_log_line(line.strip()))
                    else:
                        time.sleep(0.1)
                        
        except KeyboardInterrupt:
            print("\n停止跟踪日志")
        except Exception as e:
            print(f"跟踪日志失败: {e}")
    
    def search_logs(self, pattern: str, days: int = 1, case_sensitive: bool = False):
        """
        搜索日志内容
        
        Args:
            pattern: 搜索模式
            days: 搜索天数
            case_sensitive: 是否区分大小写
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
        
        log_files = self._get_log_files(days)
        matches = []
        
        for log_file in log_files:
            if not log_file.exists():
                continue
                
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            matches.append({
                                'file': log_file.name,
                                'line': line_num,
                                'content': line.strip()
                            })
            except Exception as e:
                print(f"搜索文件 {log_file} 失败: {e}")
        
        # 显示搜索结果
        print(f"搜索模式: {pattern}")
        print(f"找到 {len(matches)} 条匹配记录:")
        print("-" * 80)
        
        for match in matches:
            print(f"[{match['file']}:{match['line']}] {self._format_log_line(match['content'])}")
    
    def error_summary(self, days: int = 1):
        """
        错误日志摘要
        
        Args:
            days: 统计天数
        """
        error_file = self.error_log_file
        
        if not error_file.exists():
            print(f"错误日志文件不存在: {error_file}")
            return
        
        errors = []
        error_counts = {}
        
        try:
            with open(error_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        timestamp = datetime.fromisoformat(log_entry.get('timestamp', ''))
                        
                        # 过滤时间范围
                        if datetime.now(timezone(timedelta(hours=8))) - timestamp <= timedelta(days=days):
                            errors.append(log_entry)
                            
                            # 统计错误类型
                            error_type = log_entry.get('exception', {}).get('type', 'Unknown')
                            error_counts[error_type] = error_counts.get(error_type, 0) + 1
                            
                    except (json.JSONDecodeError, ValueError):
                        continue
                        
        except Exception as e:
            print(f"读取错误日志失败: {e}")
            return
        
        # 显示错误摘要
        print(f"最近 {days} 天错误摘要:")
        print(f"总错误数: {len(errors)}")
        print("-" * 50)
        
        # 显示错误类型统计
        print("错误类型统计:")
        for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {count}")
        
        print("-" * 50)
        
        # 显示最近的错误
        print("最近的错误记录:")
        recent_errors = sorted(errors, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
        
        for error in recent_errors:
            timestamp = error.get('timestamp', '')
            message = error.get('message', '')
            exception_type = error.get('exception', {}).get('type', 'Unknown')
            
            print(f"[{timestamp}] {exception_type}: {message}")
    
    def _get_log_files(self, days: int) -> List[Path]:
        """获取指定天数内的日志文件"""
        log_files = [self.app_log_file]
        
        # 添加轮转的日志文件
        for i in range(1, days + 1):
            rotated_file = self.log_dir / f'app.log.{i}'
            if rotated_file.exists():
                log_files.append(rotated_file)
        
        return log_files
    
    def _match_level(self, line: str, level: str) -> bool:
        """检查日志行是否匹配指定级别"""
        try:
            if line.startswith('{'):
                # JSON格式日志
                log_entry = json.loads(line)
                return log_entry.get('level', '').upper() == level.upper()
            else:
                # 普通格式日志
                return level.upper() in line.upper()
        except:
            return level.upper() in line.upper()
    
    def _format_log_line(self, line: str) -> str:
        """格式化日志行显示"""
        try:
            if line.startswith('{'):
                # JSON格式日志
                log_entry = json.loads(line)
                timestamp = log_entry.get('timestamp', '')
                level = log_entry.get('level', '')
                message = log_entry.get('message', '')
                logger_name = log_entry.get('logger', '')
                
                # 简化时间戳显示
                if timestamp:
                    dt = datetime.fromisoformat(timestamp)
                    timestamp = dt.strftime('%H:%M:%S')
                
                return f"[{timestamp}] {level:8} {logger_name}: {message}"
            else:
                # 普通格式日志，直接返回
                return line
        except:
            return line


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='日志查看和分析工具')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # tail 命令
    tail_parser = subparsers.add_parser('tail', help='查看日志尾部')
    tail_parser.add_argument('-n', '--lines', type=int, default=50, help='显示行数')
    tail_parser.add_argument('-f', '--follow', action='store_true', help='实时跟踪')
    tail_parser.add_argument('-l', '--level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='过滤日志级别')
    
    # search 命令
    search_parser = subparsers.add_parser('search', help='搜索日志')
    search_parser.add_argument('pattern', help='搜索模式')
    search_parser.add_argument('-d', '--days', type=int, default=1, help='搜索天数')
    search_parser.add_argument('-c', '--case-sensitive', action='store_true', help='区分大小写')
    
    # errors 命令
    errors_parser = subparsers.add_parser('errors', help='错误日志摘要')
    errors_parser.add_argument('-d', '--days', type=int, default=1, help='统计天数')
    
    # 通用参数
    parser.add_argument('--log-dir', default='./logs', help='日志目录路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    analyzer = LogAnalyzer(args.log_dir)
    
    try:
        if args.command == 'tail':
            analyzer.tail_logs(args.lines, args.follow, args.level)
        elif args.command == 'search':
            analyzer.search_logs(args.pattern, args.days, args.case_sensitive)
        elif args.command == 'errors':
            analyzer.error_summary(args.days)
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(f"执行命令失败: {e}")


if __name__ == '__main__':
    main()