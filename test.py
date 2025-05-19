import datetime

# 가상의 테스트 데이터
all_articles_test_data = {
    "테스트신문1": [
        ("테스트 기사 제목 1-1", "https://test.link.1-1"),
        ("테스트 기사 제목 1-2", "https://test.link.1-2")
    ],
    "테스트신문2": [
        ("테스트 기사 제목 2-1", "https://test.link.2-1")
    ]
}
all_articles = all_articles_test_data # 실제 크롤링 대신 테스트 데이터 사용

now = datetime.datetime.now()
filename = f"신문기사_테스트_{now.strftime('%Y%m%d_%H%M%S')}.txt"

with open(filename, "w", encoding="utf-8") as f:
    f.write("📰 오늘의 신문 기사 모음 (테스트)\n\n")

    if not all_articles:
        f.write("수집된 신문사가 없습니다.\n")
    else:
        for newspaper_name, article_tuples in all_articles.items():
            f.write(f"📌 [{newspaper_name}]\n")
            if not article_tuples:
                f.write("  수집된 기사가 없습니다.\n\n")
            else:
                for idx, (title, link) in enumerate(article_tuples, 1):
                    f.write(f" 🔹 {title}\n")
                    f.write(f"    {link}\n")
                f.write("\n")
print(f"테스트 결과를 '{filename}' 파일에 성공적으로 저장했습니다.")