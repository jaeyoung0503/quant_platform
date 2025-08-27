import os

# 설정
input_dirs = [
    r"C:\Aproject\test\quant_actual",
    # r"C:\Aproject\quant-platform\quant-trading-platform\backend",
    # r"C:\Aproject\quant-platform\src",
    # r"C:\Aproject\quant-platform\backtester"
]  # 입력 디렉토리 목록
output_file = r"C:\Aproject\quant_platform\combined_output.txt"  # 출력 파일
file_extensions = [".py", ".ts", ".tsx", ".js", ".json"]  # 포함할 파일 확장자

def combine_files():
    # 출력 파일 초기화
    with open(output_file, 'w', encoding='utf-8') as outfile:
        # 각 입력 디렉토리 순회
        for dir_path in input_dirs:
            if not os.path.exists(dir_path):
                outfile.write(f"\n{'='*50}\n")
                outfile.write(f"Directory not found: {dir_path}\n")
                outfile.write(f"{'='*50}\n")
                continue

            # 디렉토리 내 파일 순회
            for root, dirs, files in os.walk(dir_path):
                # node_modules 및 .next 디렉토리 제외
                if 'node_modules' in dirs:
                    dirs.remove('node_modules')  # node_modules 제외
                if '.next' in dirs:
                    dirs.remove('.next')  # .next 디렉토리 제외
                for file in files:
                    if any(file.endswith(ext) for ext in file_extensions):  # 지정된 확장자 확인
                        file_path = os.path.join(root, file)
                        try:
                            # 파일 내용 읽기
                            with open(file_path, 'r', encoding='utf-8') as infile:
                                content = infile.read()
                            # 출력 파일에 파일 경로와 내용 기록
                            outfile.write(f"\n{'='*50}\n")
                            outfile.write(f"File: {file_path}\n")
                            outfile.write(f"{'='*50}\n")
                            outfile.write(content)
                            outfile.write("\n\n")  # 파일 간 구분을 위한 빈 줄
                        except UnicodeDecodeError:
                            # 인코딩 오류 시 cp949 시도
                            try:
                                with open(file_path, 'r', encoding='cp949') as infile:
                                    content = infile.read()
                                outfile.write(f"\n{'='*50}\n")
                                outfile.write(f"File: {file_path} (encoded in cp949)\n")
                                outfile.write(f"{'='*50}\n")
                                outfile.write(content)
                                outfile.write("\n\n")
                            except Exception as e:
                                outfile.write(f"\n{'='*50}\n")
                                outfile.write(f"Error reading {file_path}: {str(e)}\n")
                                outfile.write(f"{'='*50}\n")
                        except Exception as e:
                            outfile.write(f"\n{'='*50}\n")
                            outfile.write(f"Error reading {file_path}: {str(e)}\n")
                            outfile.write(f"{'='*50}\n")

if __name__ == "__main__":
    combine_files()
    print(f"모든 파일이 {output_file}로 합쳐졌습니다.")