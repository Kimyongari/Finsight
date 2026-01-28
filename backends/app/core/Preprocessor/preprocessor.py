import requests
from collections import defaultdict
from langchain_core.documents import Document
import re
import fitz
from pydantic import BaseModel
from datetime import datetime
from ..llm.llm import Midm, Gemini, SK, LG, OpenRouterLLM

import json
from typing import Optional

class VectorMeta(BaseModel):
    class Config:
        extra = 'allow'

    text: Optional[str] = None
    n_char: Optional[int] = None
    n_word: Optional[int] = None
    i_page: Optional[int] = None
    i_chunk_on_page: Optional[int] = None
    n_chunk_of_page: Optional[int] = None
    i_chunk_on_doc: Optional[int] = None
    n_chunk_of_doc: Optional[int] = None
    n_page: Optional[int] = None
    name: Optional[str] = None

class DocumentProcessor:
    def __init__(self, llm_type:str = None):
        self.all_text = ''
        self.legal_name = ''
        # It's good practice to initialize all instance variables in __init__
        self.file_path = ''
        if llm_type == "SK":
            self.llm = SK()
        elif llm_type == "LG":
            self.llm = LG()
        elif llm_type == 'Gemini':
            self.llm = Gemini()
        else:
            self.llm = OpenRouterLLM()


    def name_finder(self, texts):
        system_prompt = '''당신은 법률 문서를 분석하는 전문가입니다. 사용자가 제공한 문서를 읽고, 문서 안에 기재된 법의 제목을 정확히 찾아서 출력하세요.

지침:
1. 법의 제목은 반드시 문서 안에서 직접 찾아야 합니다.
2. 제목에 '시행령', '시행세칙', '규칙', '고시' 등이 포함되어 있다면 반드시 포함하여 그대로 출력해야 합니다.
3. 해설, 설명, 부가 텍스트 등은 절대 포함하지 말고 법의 제목만 출력합니다.
4. 제목은 원문 그대로 출력하며, 단어를 생략하거나 수정하지 않습니다.
5. 문서 안에 제목이 여러 개 있을 경우, 가장 상단에 위치한 법령 제목을 선택합니다.
6. 출력은 오직 법령 제목만 한 줄로 작성합니다.

예시 입력:
개인정보 보호법 시행령
제1조(목적)
제2조(금융회사의 범위)
제3조
제4조(전자화폐의 범용성 요건)
제4조의2(가맹점의 범위)
제5조(적용범위의 예외)
...

예시 출력:
개인정보 보호법 시행령'''
        user_input = f'문서 : {texts}\n\n제목 :'
        response = self.llm.call(system_prompt=system_prompt, user_input=user_input)
        return response
        
    def load_documents(self, file_path):
        doc = fitz.open(file_path)
        return doc


    def get_structure(self, doc):
        all_text = ''
        for page in doc:
            all_text += page.get_text()
        all_text = re.sub(r'법제처\s+\d+\s+국가법령정보센터', '', all_text)
        first_page_text = doc[0].get_text()
        preview_text = first_page_text[:200] + '...'
        self.legal_name = self.name_finder(preview_text)
        pattern = r'제\s*\d+\s*조(?:의\s*\d+)?(?:\s*\([^)]+\))?'
        first_match = re.search(pattern, all_text)
        names = ''
        # 2. 첫 번째 매치가 있는지 확인
        if first_match:
            # 첫 번째 매치의 시작 위치와 정확한 텍스트(키워드)를 저장
            start_index = first_match.start()
            first_match_keyword = first_match.group(0)
            search_start_pos = first_match.end()
            second_match_index = all_text.find(first_match_keyword, search_start_pos)
            
            # 4. 두 번째 매치를 찾았는지에 따라 end_index 설정
            if second_match_index != -1:
                # 두 번째 매치를 찾았다면 그 위치를 end_index로 설정
                end_index = second_match_index
            else:
                # 찾지 못했다면 문서의 끝까지를 범위로 설정
                end_index = len(all_text)
                
            # 최종적으로 start_index와 end_index를 사용해 텍스트를 추출
            names = all_text[start_index:end_index]
        if end_index == len(all_text):
            pattern = r'제\s*1(?:\s*-\s*1)?\s*조(?:\s*\(목적\))?'
            matches = re.finditer(pattern, self.all_text)

            for idx, match in enumerate(matches):
                if idx == 0:
                    start = match.start()
                if idx == 1:
                    end = match.start()
                    break
            names = all_text[start:end]
        
        structure = defaultdict(lambda: defaultdict(dict))
        current_chapter = '목적'
        current_section = '절 없음'
        lines = names.splitlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 장 제목 찾기
            chapter_match = re.match(r'제\d+장\s+[^\n<]*', line)
            if chapter_match:
                current_chapter = chapter_match.group().strip()
                current_section = '절 없음'  # 장 바뀌면 절 리셋
                continue

            # 절 제목 찾기
            section_match = re.match(r'제\d+절\s+[^\n<]*', line)
            if section_match:
                current_section = section_match.group().strip()
                continue

            # 조문 찾기
            article_match = re.match(r'제\s*\d+(?:\s*-\s*\d+)?(?:\s*-\s*\d+)?\s*조(?:의\s*\d+)?(?:\s*\([^)]+\))?|부\s*칙', line)
            if article_match:
                article_title = article_match.group().strip()
                structure[current_chapter][current_section][article_title] = ''

        return structure
    
    def fill_structure(self, structure, doc):

        # doc = fitz.open("your_pdf_file.pdf") # PDF 파일 로드
        # structure = {...} # 기존의 structure 딕셔너리

        # --- 1. 페이지별 텍스트와 인덱스 맵 생성 ---
        all_texts = []
        page_char_map = []
        current_pos = 0

        # 헤더/푸터 제거를 위한 정규식 (필요에 따라 수정)
        header_footer_pattern = re.compile(r'법제처\s+\d+\s+국가법령정보센터')

        for page in doc:
            # 페이지 텍스트에서 헤더/푸터 제거
            page_text = header_footer_pattern.sub('', page.get_text())
            page_len = len(page_text)
            
            # 각 페이지의 정보(페이지 번호, 전체 텍스트 내 시작/끝 위치)를 저장
            page_char_map.append({
                'page_num': page.number + 1, # 페이지 번호는 0부터 시작하므로 +1
                'start': current_pos,
                'end': current_pos + page_len
            })
            
            all_texts.append(page_text)
            current_pos += page_len

        # 모든 페이지 텍스트를 하나의 문자열로 결합
        all_text = "".join(all_texts)

        # --- 유연한 패턴 생성을 위한 함수 (기존과 동일) ---
        def create_flexible_pattern(title):
            parts = re.split(r'([0-9]+|[a-zA-Z]+|[가-힣]+|\W)', title)
            parts = [p for p in parts if p and not p.isspace()]
            escaped_parts = [re.escape(p) for p in parts]
            pattern = r'\s*'.join(escaped_parts)
            return pattern

        # --- 2. 페이지 번호 조회를 위한 함수 ---
        def find_page_for_index(index, char_map):
            """문자열 인덱스가 속한 페이지 번호를 찾습니다."""
            for page_info in char_map:
                if page_info['start'] <= index < page_info['end']:
                    return page_info['page_num']
            return -1 # 찾지 못한 경우

        # --- 3. 기존 검색 로직에 페이지 번호 찾기 추가 ---
        structure_keys = list(structure.keys())

        # 마지막 조항 이후의 텍스트만 사용하는 로직 (필요시 유지)
        last_chapter = list(structure.keys())[-1]
        last_section = list(structure[last_chapter].keys())[-1]
        last_article = list(structure[last_chapter][last_section].keys())[-1]
        start_idx_match = re.search(create_flexible_pattern(last_article), all_text)
        if start_idx_match:
            all_text = all_text[start_idx_match.start():]

        search_pos = 0

        for i, chapter in enumerate(structure_keys):
            section_dict = structure[chapter]
            section_keys = list(section_dict.keys())
            
            for j, section in enumerate(section_keys):
                articles = section_dict[section]

                for k, article in enumerate(articles):
                    article_title_list = list(articles.keys())
                    current_article_title = article
                    current_pattern = create_flexible_pattern(current_article_title)
                    
                    compiled_pattern = re.compile(current_pattern, flags=0)
                    current_article_match = compiled_pattern.search(all_text, search_pos)
                    
                    if not current_article_match:
                        continue

                    current_article_index = current_article_match.start()
                    search_pos = current_article_match.end()
                    
                    # 페이지 번호를 매핑
                    page_number = find_page_for_index(current_article_index + start_idx_match.start(), page_char_map)

                    end_index = len(all_text)
                    possible_end_indexes = []

                    if k + 1 < len(articles):
                        next_article_title = article_title_list[k+1]
                        next_pattern = create_flexible_pattern(next_article_title)
                        compiled_next_pattern = re.compile(next_pattern, flags=0)
                        next_match = compiled_next_pattern.search(all_text, search_pos)
                        if next_match:
                            possible_end_indexes.append(next_match.start())

                    if j + 1 < len(section_keys):
                        next_section_articles = section_dict[section_keys[j + 1]]
                        if next_section_articles:
                            next_title = list(next_section_articles.keys())[0]
                            next_pattern = create_flexible_pattern(next_title)
                            compiled_next_pattern = re.compile(next_pattern, flags=0)
                            next_match = compiled_next_pattern.search(all_text, search_pos)
                            if next_match:
                                possible_end_indexes.append(next_match.start())

                    if i + 1 < len(structure_keys):
                        next_chapter_articles = structure[structure_keys[i + 1]]
                        if next_chapter_articles:
                            first_section_key = list(next_chapter_articles.keys())[0]
                            if next_chapter_articles[first_section_key]:
                                next_title = list(next_chapter_articles[first_section_key].keys())[0]
                                next_pattern = create_flexible_pattern(next_title)
                                compiled_next_pattern = re.compile(next_pattern, flags=0)
                                next_match = compiled_next_pattern.search(all_text, search_pos)
                                if next_match:
                                    possible_end_indexes.append(next_match.start())

                    if possible_end_indexes:
                        end_index = min(possible_end_indexes)

                    raw_text = all_text[current_article_index:end_index].strip()
                    
                    # structure에 텍스트와 함께 페이지 번호를 저장
                    structure[chapter][section][current_article_title] = {
                        'text': raw_text,
                        'page': page_number
                    }   
        return structure


    def compose_vectors(self, structure, doc):
        vectors = []
        for chapter in structure:
            for section in structure[chapter]:
                for article in structure[chapter][section]:
                    text = f'[{self.legal_name}] [{chapter}] [{section}] ' + structure[chapter][section][article]['text']
                    page = structure[chapter][section][article]['page']

                    vectors.append(VectorMeta.model_validate({
                                    'text': text,
                                    'n_char': len(text),
                                    'n_word': len(text.split()),
                                    'i_page': page,
                                    'n_page': len(doc),
                                    'name' : (self.legal_name + ' ' + article).replace(' ', ''),
                                    'reg_date': datetime.now().isoformat(timespec='seconds') + 'Z',
                                    'file_path' : self.file_path[1:] if self.file_path.startswith('.') else self.file_path,
                                    'file_name':  self.file_path.split('/')[-1]
                                }))
                    
        return vectors
    def preprocess(self, file_path: str):
        self.file_path = file_path
        documents = self.load_documents(file_path)
        
        structure = self.get_structure(documents)
        filled_structure = self.fill_structure(structure=structure, doc = documents)
        vectors = self.compose_vectors(structure, documents)
        return vectors