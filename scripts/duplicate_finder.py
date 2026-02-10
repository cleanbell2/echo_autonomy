#!/usr/bin/env python3
"""
중복 파일 찾기 및 정리 도구
MD5 해시를 사용하여 중복 파일을 찾고 정리합니다.
"""

import os
import hashlib
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def calculate_file_hash(filepath, chunk_size=8192):
    """파일의 MD5 해시를 계산합니다."""
    md5 = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5.update(chunk)
        return md5.hexdigest()
    except (IOError, PermissionError) as e:
        print(f"❌ 파일 읽기 실패: {filepath} - {e}")
        return None


def get_file_info(filepath):
    """파일 정보를 가져옵니다."""
    stat = os.stat(filepath)
    return {
        'path': str(filepath),
        'size': stat.st_size,
        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
    }


def find_duplicates(directory, exclude_dirs=None):
    """디렉토리에서 중복 파일을 찾습니다."""
    if exclude_dirs is None:
        exclude_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}
    
    hash_to_files = defaultdict(list)
    total_files = 0
    
    print(f"🔍 중복 파일 검색 중: {directory}")
    print("-" * 60)
    
    directory_path = Path(directory)
    
    # 모든 파일을 순회하며 해시 계산
    for filepath in directory_path.rglob('*'):
        # 디렉토리 제외
        if filepath.is_dir():
            continue
        
        # 제외할 디렉토리 체크
        if any(excluded in filepath.parts for excluded in exclude_dirs):
            continue
        
        # 빈 파일 제외
        if filepath.stat().st_size == 0:
            continue
        
        total_files += 1
        file_hash = calculate_file_hash(filepath)
        
        if file_hash:
            file_info = get_file_info(filepath)
            file_info['hash'] = file_hash
            hash_to_files[file_hash].append(file_info)
    
    # 중복 파일만 필터링
    duplicates = {
        hash_val: files 
        for hash_val, files in hash_to_files.items() 
        if len(files) > 1
    }
    
    print(f"✅ 총 {total_files}개 파일 검사 완료")
    print(f"📊 중복 그룹 발견: {len(duplicates)}개")
    
    return duplicates


def format_size(size_bytes):
    """바이트를 읽기 쉬운 형식으로 변환합니다."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def display_duplicates(duplicates):
    """중복 파일을 보기 좋게 출력합니다."""
    if not duplicates:
        print("\n✨ 중복 파일이 없습니다!")
        return
    
    print("\n" + "=" * 60)
    print("🔄 중복 파일 목록")
    print("=" * 60)
    
    total_wasted_space = 0
    group_num = 1
    
    for hash_val, files in duplicates.items():
        file_size = files[0]['size']
        wasted_space = file_size * (len(files) - 1)
        total_wasted_space += wasted_space
        
        print(f"\n[그룹 {group_num}] - {len(files)}개 중복 파일 ({format_size(file_size)})")
        print(f"  낭비 공간: {format_size(wasted_space)}")
        print(f"  해시: {hash_val[:16]}...")
        
        for idx, file_info in enumerate(files, 1):
            print(f"    {idx}. {file_info['path']}")
            print(f"       수정일: {file_info['modified']}")
        
        group_num += 1
    
    print("\n" + "=" * 60)
    print(f"💾 총 낭비 공간: {format_size(total_wasted_space)}")
    print("=" * 60)


def save_report(duplicates, output_file='duplicate_report.json'):
    """중복 파일 보고서를 JSON 파일로 저장합니다."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_duplicate_groups': len(duplicates),
        'duplicates': duplicates
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 보고서 저장됨: {output_file}")


def interactive_cleanup(duplicates):
    """대화형으로 중복 파일을 정리합니다."""
    if not duplicates:
        return
    
    print("\n" + "=" * 60)
    print("🧹 중복 파일 정리 모드")
    print("=" * 60)
    print("\n각 중복 그룹에서 유지할 파일을 선택하고,")
    print("나머지는 삭제할 수 있습니다.")
    print("\n명령어:")
    print("  숫자: 유지할 파일 번호 선택")
    print("  s: 이 그룹 건너뛰기")
    print("  q: 종료")
    print("-" * 60)
    
    deleted_files = []
    freed_space = 0
    
    for group_num, (hash_val, files) in enumerate(duplicates.items(), 1):
        print(f"\n[그룹 {group_num}/{len(duplicates)}]")
        print(f"파일 크기: {format_size(files[0]['size'])}")
        
        for idx, file_info in enumerate(files, 1):
            print(f"  {idx}. {file_info['path']}")
        
        while True:
            choice = input(f"\n유지할 파일 번호 (1-{len(files)}) 또는 명령어 [s/q]: ").strip().lower()
            
            if choice == 'q':
                print("\n🛑 정리 종료")
                break
            
            if choice == 's':
                print("⏭️  건너뛰기")
                break
            
            if choice.isdigit() and 1 <= int(choice) <= len(files):
                keep_idx = int(choice) - 1
                keep_file = files[keep_idx]['path']
                
                print(f"\n✅ 유지: {keep_file}")
                print("🗑️  삭제할 파일:")
                
                for idx, file_info in enumerate(files):
                    if idx != keep_idx:
                        print(f"    - {file_info['path']}")
                
                confirm = input("\n삭제를 진행하시겠습니까? (y/N): ").strip().lower()
                
                if confirm == 'y':
                    for idx, file_info in enumerate(files):
                        if idx != keep_idx:
                            try:
                                os.remove(file_info['path'])
                                deleted_files.append(file_info['path'])
                                freed_space += file_info['size']
                                print(f"  ✓ 삭제됨: {file_info['path']}")
                            except Exception as e:
                                print(f"  ✗ 삭제 실패: {file_info['path']} - {e}")
                    print(f"\n💾 확보된 공간: {format_size(freed_space)}")
                else:
                    print("❌ 삭제 취소")
                
                break
            else:
                print("⚠️  올바른 번호나 명령어를 입력하세요.")
        
        if choice == 'q':
            break
    
    # 정리 요약
    if deleted_files:
        print("\n" + "=" * 60)
        print("📊 정리 완료 요약")
        print("=" * 60)
        print(f"삭제된 파일: {len(deleted_files)}개")
        print(f"확보된 공간: {format_size(freed_space)}")
        print("\n삭제된 파일 목록:")
        for filepath in deleted_files:
            print(f"  - {filepath}")
    else:
        print("\n📝 삭제된 파일이 없습니다.")


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='중복 파일 찾기 및 정리 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='검색할 디렉토리 (기본값: 현재 디렉토리)'
    )
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='대화형 정리 모드'
    )
    parser.add_argument(
        '-r', '--report',
        metavar='FILE',
        help='보고서를 JSON 파일로 저장'
    )
    parser.add_argument(
        '-e', '--exclude',
        nargs='+',
        help='제외할 디렉토리 이름'
    )
    
    args = parser.parse_args()
    
    # 중복 파일 찾기
    exclude_dirs = set(args.exclude) if args.exclude else None
    duplicates = find_duplicates(args.directory, exclude_dirs)
    
    # 결과 출력
    display_duplicates(duplicates)
    
    # 보고서 저장
    if args.report:
        save_report(duplicates, args.report)
    
    # 대화형 정리
    if args.interactive and duplicates:
        interactive_cleanup(duplicates)


if __name__ == '__main__':
    main()
