import os
import re
import glob

def process_cbt_list_files():
    list_dir = os.path.join(os.path.dirname(__file__), 'CBT-list')
    if not os.path.exists(list_dir):
        print("CBT-list directory not found.")
        return

    html_files = glob.glob(os.path.join(list_dir, '*.html'))
    print(f"Found {len(html_files)} list files in CBT-list")

    count = 0
    for file_path in html_files:
        file_name = os.path.basename(file_path)
        exam_name = file_name.replace('-list.html', '').replace('-', ' ')

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Check if already processed
        if 'BreadcrumbList' in content:
            continue

        # Build JSON-LD Breadcrumb & Quiz Schema
        schema_code = f'''    <!-- 구글 1위 노출용 Breadcrumb & Quiz Schema -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{ "@type": "ListItem", "position": 1, "name": "홈", "item": "https://cbtkorea.kr/" }},
        {{ "@type": "ListItem", "position": 2, "name": "기출문제", "item": "https://cbtkorea.kr/exams.html" }},
        {{ "@type": "ListItem", "position": 3, "name": "{exam_name} 기출문제", "item": "https://cbtkorea.kr/CBT-list/{file_name}" }}
      ]
    }}
    </script>
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Quiz",
      "name": "{exam_name} CBT 기출문제 모의고사",
      "description": "{exam_name} 자격증 필기 시험 기출문제 무료 모의고사 및 문제풀이 - cbtkorea.kr",
      "educationalUse": "Exam Practice",
      "provider": {{
        "@type": "Organization",
        "name": "CBT 기출문제",
        "url": "https://cbtkorea.kr/"
      }}
    }}
    </script>
'''

        # Inject schema before </head>
        if '</head>' in content:
            content = content.replace('</head>', f'{schema_code}</head>', 1)

        # Inject Breadcrumb UI before <h1
        breadcrumb_ui = f'''<nav class="text-sm font-medium text-gray-500 mb-4" aria-label="Breadcrumb">
            <ol class="inline-flex items-center space-x-1 md:space-x-2">
                <li><a href="../index.html" class="text-blue-600 hover:text-blue-800 flex items-center"><i class="fas fa-home mr-1 text-xs"></i>홈</a></li>
                <li><i class="fas fa-chevron-right text-gray-400 mx-1 text-xs"></i></li>
                <li><a href="../exams.html" class="text-blue-600 hover:text-blue-800">기출문제</a></li>
                <li><i class="fas fa-chevron-right text-gray-400 mx-1 text-xs"></i></li>
                <li class="text-gray-800 font-bold" aria-current="page">{exam_name}</li>
            </ol>
        </nav>
'''
        if '<h1' in content and 'Breadcrumb' not in content:
            content = re.sub(r'(<h1[^>]*>)', r'{}\1'.format(breadcrumb_ui), content, count=1)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        count += 1

    print(f"Successfully processed {count} CBT list files.")

if __name__ == '__main__':
    process_cbt_list_files()
