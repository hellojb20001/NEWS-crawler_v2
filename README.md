# 신문 기사 수집기 pro

한국의 주요 신문사들의 기사를 한눈에 모아보는 웹 애플리케이션입니다. 향상된 크롤링 속도와 사용자 편의 기능을 제공합니다.

## 주요 기능

-   경제 신문, 종합일간지, 석간 신문 그룹별 기사 수집
-   선택한 신문사들에 대한 **병렬 크롤링 지원**으로 수집 속도 향상
-   전체 기사 또는 1면 기사만 선택적 수집
-   실시간 크롤링 진행 상태 확인 (진행률 표시)
-   수집된 기사 목록을 웹 화면에서 즉시 확인
-   결과 내 **기사 제목 검색 및 필터링 기능** (검색 버튼 클릭 또는 Enter 키 입력, 초기화 기능 포함)
-   수집된 기사 전체 또는 필터링된 결과에 대해 클립보드 복사 및 텍스트 파일 저장 기능
-   사용자 친화적인 웹 인터페이스

## 설치 방법

1.  **저장소 클론**
    ```bash
    git clone [https://github.com/yourusername/news-crawler-pro.git](https://github.com/yourusername/news-crawler-pro.git)
    cd news-crawler-pro
    ```

2.  **가상환경 생성 및 활성화**
    ```bash
    python -m venv venv
    ```
    -   Linux/Mac:
        ```bash
        source venv/bin/activate
        ```
    -   Windows:
        ```bash
        venv\Scripts\activate
        ```

3.  **필요한 패키지 설치**
    ```bash
    pip install -r requirements.txt
    ```
    * `requirements.txt`에는 `selenium`, `flask` 등의 필수 패키지가 포함되어 있습니다.

4.  **Chrome WebDriver 설치**
    -   로컬 시스템에 Chrome 브라우저가 설치되어 있어야 합니다.
    -   Selenium이 Chrome 브라우저를 제어하기 위해 ChromeDriver가 필요합니다. 다음 두 가지 방법 중 하나를 선택하세요:
        1.  **방법 1 (권장: `webdriver-manager` 사용)**:
            -   `webdriver-manager`는 현재 설치된 Chrome 브라우저 버전에 맞는 ChromeDriver를 자동으로 다운로드하고 관리합니다.
            -   먼저 `webdriver-manager`를 설치합니다:
                ```bash
                pip install webdriver-manager
                ```
            -   그다음, `app.py` 파일 내의 `setup_chrome_driver` 함수에서 `webdriver_manager`를 사용하도록 관련 주석을 참고하여 코드를 수정/활성화합니다. (예: `Service(ChromeDriverManager().install())` 사용)
            -   `requirements.txt` 파일에도 `webdriver-manager`를 추가하는 것이 좋습니다.
        2.  **방법 2 (수동 설정)**:
            -   [ChromeDriver 공식 다운로드 페이지](https://chromedriver.chromium.org/downloads)에서 사용자의 Chrome 브라우저 버전에 정확히 일치하는 ChromeDriver를 수동으로 다운로드합니다.
            -   다운로드한 `chromedriver.exe` (Windows) 또는 `chromedriver` (Linux/Mac) 실행 파일을 시스템 PATH 환경 변수에 등록된 디렉터리로 옮기거나, `app.py`의 `setup_chrome_driver` 함수 내에서 해당 실행 파일의 전체 경로를 직접 지정합니다. (현재 제공된 `app.py` 코드는 시스템 PATH에 설정된 ChromeDriver를 우선적으로 찾도록 되어 있습니다.)

## 실행 방법

1.  터미널 또는 명령 프롬프트에서 다음 명령어를 실행합니다:
    ```bash
    python app.py
    ```
2.  애플리케이션이 실행되면, 웹 브라우저를 열고 주소창에 `http://localhost:5000`을 입력하여 접속합니다.

**참고 사항:**
-   개발 환경에서 실행 시, `app.py`의 `app.run()` 함수에 `use_reloader=False` 옵션이 적용되어 있어 `multiprocessing`과의 호환성을 높였습니다.
-   프로덕션(실서비스) 환경에서는 Flask 개발 서버 대신 Gunicorn, uWSGI 등과 같은 전문 WSGI 서버를 사용하여 애플리케이션을 배포하는 것을 강력히 권장합니다.

## 사용 방법

1.  **신문사 선택**:
    -   웹 페이지 접속 후, '경제 신문', '종합일간지(조간)', '석간 신문' 각 그룹에서 수집을 원하는 신문사를 하나 이상 선택합니다.
    -   각 그룹 상단의 '전체 선택' 체크박스를 사용하여 해당 그룹의 모든 신문사를 한 번에 선택하거나 해제할 수 있습니다.
2.  **수집 범위 선택**:
    -   드롭다운 메뉴에서 '전체 기사' 또는 '1면 기사만' 중 원하는 수집 범위를 선택합니다.
3.  **크롤링 시작**:
    -   '크롤링 시작' 버튼을 클릭합니다.
    -   선택된 설정에 따라 기사 수집이 시작되며, 화면에 진행률과 현재 처리 중인 작업 상태가 표시됩니다.
4.  **결과 확인 및 활용**:
    -   크롤링이 완료되면, 수집된 기사 목록이 신문사별로 구분되어 화면 하단에 나타납니다.
    -   **기사 제목 검색**:
        -   결과 목록 상단에 위치한 검색창에 원하는 키워드를 입력합니다.
        -   '검색' 버튼을 클릭하거나, 검색창에서 Enter 키를 누르면 해당 키워드가 제목에 포함된 기사들만 필터링되어 표시됩니다.
    -   **검색 초기화**:
        -   '초기화' 버튼을 클릭하면 현재 적용된 검색 필터가 해제되고, 수집된 전체 기사 목록이 다시 나타납니다.
    -   **결과 복사**:
        -   '복사' 버튼을 클릭하면 현재 화면에 보이는 (필터링된 경우, 필터링된 결과) 기사 목록이 텍스트 형식으로 클립보드에 복사됩니다.
    -   **결과 저장**:
        -   '저장' 버튼을 클릭하면 현재 화면에 보이는 기사 목록이 `수집된_신문기사_날짜.txt` 형식의 텍스트 파일로 다운로드됩니다.

## 기술 스택

-   **Backend**: Python 3.8+, Flask
-   **Crawling**: Selenium
-   **Concurrency**: Multiprocessing (Python Standard Library)
-   **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
-   **Python Package Management**: pip

## 라이선스

본 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 `LICENSE` 파일을 참고하십시오. (LICENSE 파일이 없다면 이 문장은 생략 가능)

## 기여하기

프로젝트에 기여하고 싶으시다면 다음 단계를 따라주세요:

1.  본 저장소를 Fork합니다.
2.  새로운 기능 또는 버그 수정을 위한 브랜치를 생성합니다. (`git checkout -b feature/AmazingFeature` 또는 `bugfix/IssueNumber`)
3.  변경 사항을 커밋합니다. (`git commit -m 'Add some AmazingFeature'`)
4.  생성한 브랜치로 Push합니다. (`git push origin feature/AmazingFeature`)
5.  Pull Request를 생성하여 변경 사항에 대한 리뷰를 요청합니다.

버그 리포트나 기능 제안은 언제나 환영입니다! GitHub 이슈를 통해 제출해주세요.