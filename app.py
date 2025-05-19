import json
import datetime # app.py에서도 datetime을 사용하기 위해 추가 (선택 사항, 파일명 생성 로직이 제거되었으므로 현재는 불필요)
import random
import time
from flask import Flask, render_template, request, jsonify
from news.newsbrief_all import crawl_newspaper_articles # news 폴더 안의 newsbrief_all.py에서 함수를 가져옵니다.
from config import newspaper_groups # config.py에서 신문사 그룹 정보를 가져옵니다.
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service # webdriver_manager 사용 시 필요
# from webdriver_manager.chrome import ChromeDriverManager # webdriver_manager 사용 시 필요
from multiprocessing import Pool, Manager, cpu_count # multiprocessing 추가

app = Flask(__name__)

# --- 신문사 그룹 정의 ---
all_papers_list = []
seen_oids = set()
for group_key in newspaper_groups:
    if group_key != 'all':
        for name, oid in newspaper_groups[group_key]:
            if oid not in seen_oids:
                all_papers_list.append((name, oid))
                seen_oids.add(oid)
newspaper_groups['all'] = sorted(list(set(all_papers_list)))

def setup_chrome_driver():
    """Chrome WebDriver 설정을 위한 함수 (각 프로세스에서 호출됨)"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--start-maximized")
    # 특정 User-Agent가 차단을 유발하는 경우가 아니라면, Selenium 기본 User-Agent나 더 일반적인 User-Agent를 사용하는 것이 좋을 수 있습니다.
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36") # User-Agent 업데이트
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-gpu') # 일부 시스템에서 headless 안정성 및 성능 향상
    chrome_options.add_argument('--no-sandbox') # Docker 또는 CI 환경에서 필요할 수 있음
    chrome_options.add_argument('--disable-dev-shm-usage') # Docker 또는 CI 환경에서 리소스 부족 문제 방지
    chrome_options.add_argument('--log-level=3') # 콘솔 로그 레벨 설정 (오류만 표시)
    chrome_options.add_argument('--blink-settings=imagesEnabled=false') # 이미지 로딩 비활성화 (속도 향상)

    # WebDriver 경로 자동 관리를 위해 webdriver_manager 사용을 권장합니다.
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    # 시스템 PATH에 ChromeDriver가 설정되어 있다고 가정
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"WebDriver 설정 중 오류 발생: {e}")
        # webdriver_manager 사용 예시 (주석 해제 후 사용)
        # from selenium.webdriver.chrome.service import Service
        # from webdriver_manager.chrome import ChromeDriverManager
        # print("webdriver_manager를 사용하여 ChromeDriver를 설정합니다.")
        # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        raise # 오류를 다시 발생시켜 호출한 쪽에서 처리하도록 함
    return driver

# 병렬 처리를 위한 작업자 함수
def crawl_worker(args):
    """
    단일 신문사 크롤링 작업을 수행하는 함수 (각 프로세스에서 실행).
    결과로 (신문사명, 기사 리스트) 또는 (신문사명, 에러 정보)를 반환.
    """
    newspaper_name, oid, crawl_scope, process_id = args
    print(f"[Process-{process_id}] '{newspaper_name}' (OID: {oid}) 크롤링 시작. 범위: {crawl_scope}")
    driver = None
    try:
        driver = setup_chrome_driver()
        articles_list = crawl_newspaper_articles(driver, newspaper_name, oid, crawl_scope)
        print(f"[Process-{process_id}] '{newspaper_name}' 크롤링 완료. 수집된 기사 수: {len(articles_list)}")
        return (newspaper_name, articles_list)
    except Exception as e:
        print(f"[Process-{process_id}] '{newspaper_name}' 크롤링 중 오류 발생: {e}")
        # 오류 발생 시 빈 리스트나 특정 오류 메시지 반환 가능
        return (newspaper_name, [("오류 발생: " + str(e), "")])
    finally:
        if driver:
            print(f"[Process-{process_id}] '{newspaper_name}' WebDriver 종료.")
            driver.quit()

@app.route('/')
def index():
    """메인 페이지를 렌더링합니다."""
    return render_template('index.html', newspaper_groups=newspaper_groups)

@app.route('/crawl', methods=['POST'])
def crawl():
    """선택된 신문사의 기사를 병렬로 크롤링하고 결과를 반환합니다."""
    selected_newspapers_json = request.form.get('selected_newspapers', '[]')
    try:
        selected_newspapers = json.loads(selected_newspapers_json)
    except json.JSONDecodeError:
        return jsonify({'error': '잘못된 신문사 선택 형식입니다.'}), 400
        
    crawl_scope = request.form.get('scope', '전체')
    
    if not selected_newspapers:
        return jsonify({'error': '신문사를 선택해주세요.'}), 400
    
    newspaper_oid_map = {}
    for group_list in newspaper_groups.values():
        for name, oid_val in group_list: # 변수명 oid가 함수 인자 oid와 겹치지 않도록 oid_val로 변경
            newspaper_oid_map[name] = oid_val
    
    all_articles_from_workers = {}
    
    # 병렬 처리를 위한 작업 인자 준비
    tasks = []
    for i, newspaper_name in enumerate(selected_newspapers):
        if newspaper_name in newspaper_oid_map:
            oid = newspaper_oid_map[newspaper_name]
            tasks.append((newspaper_name, oid, crawl_scope, i + 1)) # 각 작업에 고유 ID (process_id) 부여
        else:
            print(f"경고: '{newspaper_name}'에 대한 OID를 찾을 수 없습니다.")
            all_articles_from_workers[newspaper_name] = [("OID를 찾을 수 없는 신문사입니다.", "")]

    if not tasks: # OID를 찾을 수 없는 신문사만 선택된 경우
        if all_articles_from_workers: # OID 못찾은 신문사 정보라도 반환
             return jsonify({
                'success': True,
                'articles': all_articles_from_workers
            })
        return jsonify({'error': '크롤링할 유효한 신문사가 없습니다.'}), 400

    # CPU 코어 수를 고려하여 적절한 프로세스 수 설정 (너무 많으면 오히려 성능 저하 및 서버 부하)
    # 시스템 환경에 따라 적절한 값을 찾아야 합니다. 여기서는 최대 4개 또는 CPU 코어 수 중 작은 값을 사용합니다.
    num_processes = min(max(1, cpu_count() // 2), 4) # 최소 1개, 최대 4개 또는 CPU 코어의 절반
    if len(tasks) < num_processes: # 작업 수보다 프로세스 수가 많을 필요 없음
        num_processes = len(tasks)
    
    print(f"병렬 크롤링 시작: {len(tasks)}개 신문사, {num_processes}개 프로세스 사용 예정")

    start_time = time.time()
    
    try:
        with Pool(processes=num_processes) as pool:
            # pool.map은 단일 인자만 받으므로, crawl_worker가 단일 튜플을 받도록 수정했음
            results = pool.map(crawl_worker, tasks)
        
        for newspaper_name_result, articles_list_result in results:
            all_articles_from_workers[newspaper_name_result] = articles_list_result
            
        # --- 자동 파일 저장 로직은 현재 비활성화 상태 유지 ---
        # print(f"자동 파일 저장 비활성화됨. 결과는 웹 화면으로 전송됩니다.")
        
        end_time = time.time()
        print(f"총 크롤링 소요 시간: {end_time - start_time:.2f} 초")

        return jsonify({
            'success': True,
            'articles': all_articles_from_workers
        })
        
    except Exception as e:
        print(f"크롤링 중 심각한 오류 발생: {e}")
        # 부분적인 결과라도 있으면 반환 (선택 사항)
        if all_articles_from_workers:
             print("--- 오류 발생 시점의 부분 결과 (최대 2개 항목) ---")
             for newspaper, articles_data in all_articles_from_workers.items():
                 print(f"[{newspaper}]")
                 for i, article_tuple in enumerate(articles_data[:2]):
                     print(f"  {i+1}: {article_tuple}")
             print("----------------------------------------------------")
        return jsonify({'error': f'서버 내부 오류: {str(e)}'}), 500
    # finally 블록에서 메인 드라이버를 종료할 필요가 없음 (각 프로세스에서 관리)

if __name__ == '__main__':
    # 멀티프로세싱 사용 시 __main__ 보호 필수 (특히 Windows)
    # Flask 개발 서버는 기본적으로 디버그 모드에서 reloader를 사용하는데,
    # 이는 멀티프로세싱과 충돌을 일으킬 수 있습니다.
    # 프로덕션 환경에서는 Gunicorn과 같은 WSGI 서버를 사용해야 합니다.
    # 개발 중에는 use_reloader=False 옵션을 고려할 수 있습니다.
    app.run(debug=True, use_reloader=False) # use_reloader=False 추가


# 기존 코드 

# from flask import Flask, render_template, request, jsonify
# from news.newsbrief_all import crawl_newspaper_articles # news 폴더 안의 newsbrief_all.py에서 함수를 가져옵니다.
# from config import newspaper_groups # config.py에서 신문사 그룹 정보를 가져옵니다.
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# # from selenium.webdriver.chrome.service import Service # webdriver_manager 사용 시 필요
# # from webdriver_manager.chrome import ChromeDriverManager # webdriver_manager 사용 시 필요
# import datetime
# import random
# import time
# import json

# app = Flask(__name__)

# # --- 신문사 그룹 정의 ---
# # config.py에서 가져온 newspaper_groups를 사용합니다.
# # 'all' 그룹은 필요시 여기서 (재)구성할 수 있습니다.
# all_papers_list = []
# seen_oids = set()
# for group_key in newspaper_groups:
#     if group_key != 'all': 
#         for name, oid in newspaper_groups[group_key]:
#             if oid not in seen_oids:
#                 all_papers_list.append((name, oid))
#                 seen_oids.add(oid)
# newspaper_groups['all'] = sorted(list(set(all_papers_list)))

# def setup_chrome_driver():
#     """Chrome WebDriver 설정을 위한 함수"""
#     chrome_options = Options()
#     chrome_options.add_argument("--headless")
#     chrome_options.add_argument("--start-maximized")
#     chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
#     chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     chrome_options.add_experimental_option('useAutomationExtension', False)
#     chrome_options.add_argument('--disable-blink-features=AutomationControlled')
#     # WebDriver 경로 자동 관리를 위해 webdriver_manager 사용을 권장합니다.
#     # 아래 주석 처리된 코드를 사용하거나, 시스템 PATH에 ChromeDriver가 설정되어 있어야 합니다.
#     # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
#     return webdriver.Chrome(options=chrome_options)

# @app.route('/')
# def index():
#     """메인 페이지를 렌더링합니다."""
#     return render_template('index.html', newspaper_groups=newspaper_groups)

# @app.route('/crawl', methods=['POST'])
# def crawl():
#     """선택된 신문사의 기사를 크롤링하고 결과를 반환합니다."""
#     selected_newspapers = json.loads(request.form.get('selected_newspapers', '[]'))
#     crawl_scope = request.form.get('scope', '전체')
    
#     if not selected_newspapers:
#         return jsonify({'error': '신문사를 선택해주세요.'}), 400
    
#     newspaper_oid_map = {}
#     for group_list in newspaper_groups.values():
#         for name, oid in group_list:
#             newspaper_oid_map[name] = oid
    
#     all_articles = {}
#     driver = None
    
#     try:
#         driver = setup_chrome_driver()
#         for newspaper_name in selected_newspapers:
#             if newspaper_name in newspaper_oid_map:
#                 oid = newspaper_oid_map[newspaper_name]
#                 articles_list = crawl_newspaper_articles(driver, newspaper_name, oid, crawl_scope)
#                 all_articles[newspaper_name] = articles_list
#                 time.sleep(random.uniform(1.0, 2.5))
#             else:
#                 print(f"경고: '{newspaper_name}'에 대한 OID를 찾을 수 없습니다.")
#                 all_articles[newspaper_name] = [("OID를 찾을 수 없는 신문사입니다.", "")]

#         # --- 자동 파일 저장 로직 제거 ---
#         # # Generate filename
#         # now = datetime.datetime.now()
#         # filename = f"신문기사_{now.strftime('%Y%m%d_%H%M%S')}.txt"
        
#         # # Save results to file
#         # with open(filename, "w", encoding="utf-8") as f:
#         #     f.write("📰 오늘의 신문 기사 모음\n\n")
            
#         #     if not all_articles:
#         #         f.write("수집된 신문사가 없습니다.\n")
#         #     else:
#         #         for newspaper_name_from_dict, article_tuples in all_articles.items():
#         #             f.write(f"📌 [{newspaper_name_from_dict}]\n")
#         #             if not article_tuples:
#         #                 f.write("  수집된 기사가 없습니다.\n")
#         #             else:
#         #                 for idx, (title, link) in enumerate(article_tuples, 1):
#         #                     # 서버 콘솔에 디버깅 메시지 출력 (실제 저장되는 내용 확인용)
#         #                     # print(f"DEBUG: Would save to file - Title: '{title}', Link: '{link}'") # 필요시 주석 해제
#         #                     f.write(f" 🔹 {title}\n")
#         #                     if link and str(link).strip():
#         #                         f.write(f"    {str(link).strip()}\n")
#         #                     else:
#         #                         f.write(f"    [링크 정보 없음]\n")
#         #             f.write("\n")
#         # print(f"자동 파일 저장 비활성화됨. 결과는 웹 화면으로 전송됩니다.")
#         # --- 자동 파일 저장 로직 제거 완료 ---
        
#         # 클라이언트(웹 브라우저)에 JSON 형태로 결과 반환
#         return jsonify({
#             'success': True,
#             # 'filename': filename, # 자동 저장 파일명이 없으므로 이 부분도 주석 처리하거나 제거
#             'articles': all_articles 
#         })
        
#     except Exception as e:
#         print(f"Error during crawl: {e}")
#         if all_articles:
#             print("--- Error context: all_articles (first 2 items per newspaper) ---")
#             for newspaper, articles_data in all_articles.items():
#                 print(f"[{newspaper}]")
#                 for i, article_tuple in enumerate(articles_data[:2]):
#                     print(f"  {i+1}: {article_tuple}")
#             print("-----------------------------------------------------------------")
#         return jsonify({'error': str(e)}), 500
#     finally:
#         if driver:
#             driver.quit()

# if __name__ == '__main__':
#     app.run(debug=True)
