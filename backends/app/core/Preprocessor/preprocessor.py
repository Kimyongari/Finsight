import requests
from langchain.text_splitter import RecursiveCharacterTextSplitter
from collections import defaultdict
from langchain_core.documents import Document
import re
import fitz
from pydantic import BaseModel
from datetime import datetime
from ..llm.llm import Midm

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
    def __init__(self):
        self.all_text = ''
        self.legal_name = ''
        # It's good practice to initialize all instance variables in __init__
        self.file_path = ''
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)


    def name_finder(self, texts):
        model = Midm()
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
        response = model.call(system_prompt=system_prompt, user_input=user_input)
        return response
        
    def load_documents(self, file_path):
        doc = fitz.open(file_path)
        return doc

    def split_documents(self, doc):
        for page in doc:
            self.all_text += page.get_text()
        
        first_page_text = doc[0].get_text()
        preview_text = first_page_text[:200] + '...'
        
        # This logic for finding the table of contents is brittle.
        # It assumes '제1조(목적)' appears at least twice.
        # Consider a more robust method if documents vary.
        start = self.all_text.find('제1조(목적)')
        if start == -1:
            # Handle case where '제1조(목적)' is not found
            # For now, we'll assume the structure part is empty
            names = ""
        else:
            # Find the next '제1조(목적)' to isolate the table of contents
            end_search_start = start + len('제1조(목적)')
            end = self.all_text[end_search_start:].find('제1조(목적)')
            
            if end != -1:
                end += end_search_start # Adjust end index to be relative to the whole string
                names = self.all_text[start:end]
                self.all_text = self.all_text[end:]
            else:
                # If there's only one "제1조(목적)", assume the ToC is not present in this format
                names = ""
                self.all_text = self.all_text[start:]


        self.legal_name = self.name_finder(preview_text)
        
        lines = names.splitlines()
        structure = defaultdict(lambda: defaultdict(list))

        # ### FIX: INITIALIZE VARIABLES ###
        # Initialize with a default placeholder before the loop
        current_chapter = '장 없음' # "No Chapter"
        current_section = '절 없음' # "No Section"

        for line in lines:
            line = line.strip()
            if not line:
                continue

            chapter_match = re.match(r'제\s*\d+\s*장\s*[^\n<]*', line, flags=0)
            if chapter_match:
                current_chapter = chapter_match.group().strip()
                current_section = '절 없음'  # Reset section when a new chapter starts
                continue

            section_match = re.match(r'제\s*\d+\s*절\s*[^\n<]*', line, flags=0)
            if section_match:
                current_section = section_match.group().strip()
                continue

            article_match = re.match(r'제\s*\d+\s*조(?:의\s*\d+)?\s*\([^)]+\)|부\s*칙|제\s*\d+\s*조', line, flags=0)
            if article_match:
                # Now, current_chapter and current_section are guaranteed to have a value
                structure[current_chapter][current_section].append({f'{article_match.group().strip()}':''})
        self.test = structure
        return structure


    def compose_vectors(self, structure, doc):
        def create_flexible_pattern(title):
            parts = re.split(r'([0-9]+|[a-zA-Z]+|[가-힣]+|\W)', title)
            parts = [p for p in parts if p and not p.isspace()]
            escaped_parts = [re.escape(p) for p in parts]
            pattern = r'\s*'.join(escaped_parts)
            return pattern
            
        vectors = []
        structure_keys = list(structure.keys())
        chunk_idx = 0
        page_chunk_info = {}
        
        all_text = "".join([page.get_text() for page in doc])
        last_chapter = list(structure.keys())[-1]
        last_section = list(structure[last_chapter].keys())[-1]
        last_article = list(structure[last_chapter][last_section][-1].keys())[-1]
        start_idx = all_text.find(last_article) + 1
        all_text = all_text[start_idx:]
        search_pos = 0

        for i, chapter in enumerate(structure_keys):
            section_dict = structure[chapter]
            section_keys = list(section_dict.keys())
            
            for j, section in enumerate(section_keys):
                articles = section_dict[section]

                for k, article_dict in enumerate(articles):
                    current_article_title = list(article_dict.keys())[0]
                    current_pattern = create_flexible_pattern(current_article_title)
                    
                    compiled_pattern = re.compile(current_pattern, flags=0)
                    current_article_match = compiled_pattern.search(all_text, search_pos)
                    
                    if not current_article_match:
                        continue

                    current_article_index = current_article_match.start()
                    search_pos = current_article_match.end()

                    end_index = len(all_text)
                    possible_end_indexes = []

                    if k + 1 < len(articles):
                        next_article_title = list(articles[k + 1].keys())[0]
                        next_pattern = create_flexible_pattern(next_article_title)
                        compiled_next_pattern = re.compile(next_pattern, flags=0)
                        next_match = compiled_next_pattern.search(all_text, search_pos)
                        if next_match:
                            possible_end_indexes.append(next_match.start())

                    if j + 1 < len(section_keys):
                        next_section_articles = section_dict[section_keys[j + 1]]
                        if next_section_articles:
                            next_title = list(next_section_articles[0].keys())[0]
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
                               next_title = list(next_chapter_articles[first_section_key][0].keys())[0]
                               next_pattern = create_flexible_pattern(next_title)
                               compiled_next_pattern = re.compile(next_pattern, flags=0)
                               next_match = compiled_next_pattern.search(all_text, search_pos)
                               if next_match:
                                   possible_end_indexes.append(next_match.start())

                    if possible_end_indexes:
                        end_index = min(possible_end_indexes)

                    raw_text = all_text[current_article_index:end_index].strip()
                    chunks = self.splitter.split_text(raw_text)

                    for chunk_on_page_idx, chunk_text in enumerate(chunks):
                        page_index = -1
                        for p_idx, page in enumerate(doc):
                            test_str = chunk_text.strip()[:20].strip()
                            if test_str and test_str in page.get_text():
                                page_index = p_idx
                                break
                        
                        page_chunk_info.setdefault(page_index, 0)
                        i_chunk_on_page = page_chunk_info[page_index]
                        page_chunk_info[page_index] += 1
                        
                        # ### FIX: LOGIC CORRECTION ###
                        # The original `if chapter == '목적'` would never be true.
                        # Using the default value '장 없음' is more robust.
                        if chapter == '장 없음':
                            chunk_with_title = f'[{self.legal_name}] [{current_article_title}] {chunk_text}'
                        else:
                            chunk_with_title = f'[{self.legal_name}] [{chapter}] [{section}] [{current_article_title}] {chunk_text}'
                        
                        name = (self.legal_name + current_article_title).replace(' ', '')
                        
                        vectors.append(VectorMeta.model_validate({
                            'text': chunk_with_title,
                            'n_char': len(chunk_text),
                            'n_word': len(chunk_text.split()),
                            'i_page': page_index + 1 if page_index != -1 else -1,
                            'i_chunk_on_page': i_chunk_on_page,
                            'n_chunk_of_page': 0,
                            'i_chunk_on_doc': chunk_idx + 1,
                            'n_chunk_of_doc': 0,
                            'n_page': len(doc),
                            'name' : name,
                            'file_path' : self.file_path[1:] if self.file_path.startswith('.') else self.file_path,
                            'file_name' : self.file_path.split('/')[-1]
                        }))
                        chunk_idx += 1

        total_chunks = len(vectors)
        page_chunk_counts = defaultdict(int)
        for vector in vectors:
            if vector.i_page != -1:
                page_chunk_counts[vector.i_page] += 1
        
        for vector in vectors:
            vector.n_chunk_of_doc = total_chunks
            if vector.i_page != -1:
                vector.n_chunk_of_page = page_chunk_counts[vector.i_page]

        return vectors
    
    def preprocess(self, file_path: str):
        self.file_path = file_path
        documents = self.load_documents(file_path)
        structure = self.split_documents(documents)
        vectors = self.compose_vectors(structure, documents)
        return vectors