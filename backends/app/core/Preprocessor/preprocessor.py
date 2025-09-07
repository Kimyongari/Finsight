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

class DocumentProcessor:
    def __init__(self):
        self.all_text = ''
        self.lagal_name = ''

    def name_finder(self, texts):
        model = Midm()
        system_prompt = '''당신은 법률 전문가입니다. 사용자가 건넨 문서를 읽고 법의 제목을 찾아 주세요.
                문서의 제목은 문서 안에서 찾으세요.
                해설은 필요 없으며, 문서의 제목만 말해 주세요.'''
        user_input = f'문서 : {texts}\n\n제목 :'
        response = model.call(system_prompt=system_prompt, user_input=user_input)
        return response
        
    def load_documents(self,file_path):
        doc = fitz.open(file_path)
        return doc

    def split_documents(self, doc):
        for page in doc:
            self.all_text += page.get_text()
        
        start = self.all_text.find('제1조(목적)')
        end = self.all_text[start+7:].find('제1조(목적)')
        names = self.all_text[start:end+7]
        self.legal_name = self.name_finder(names)
        self.all_text = self.all_text[end:]

        lines = names.splitlines()
        structure = defaultdict(lambda: defaultdict(list))

        current_chapter = '목적'
        current_section = '절 없음'

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
            article_match = re.match(r'제\d+조(\의\d+)?\s*\([^)]+\)', line)
            if article_match:
                structure[current_chapter][current_section].append({f'{article_match.group().strip()}':''})
        return structure


    def compose_vectors(self, structure, doc):
        self.splitter = RecursiveCharacterTextSplitter(chunk_size = 1000,chunk_overlap = 200)
        vectors = []
        structure_keys = list(structure.keys())
        chunk_idx = 0  # 문서 전체 chunk 인덱스
        total_chunks = 0
        page_chunk_info = {}  # 각 페이지별 chunk 수 저장용
        index = 2
        all_text = self.all_text
        for i, d in enumerate(doc):
            if all_text[:100] in d.get_text():
                doc = doc[i:]
                index = i
                break


        for i, chapter in enumerate(structure_keys):
            section_dict = structure[chapter]
            section_keys = list(section_dict.keys())

            next_chapter_index = (
                all_text.find(structure_keys[i+1]) if i + 1 < len(structure_keys) else len(all_text)
            )

            for j, section in enumerate(section_keys):
                articles = section_dict[section]

                if j + 1 < len(section_keys):
                    next_section_articles = section_dict[section_keys[j+1]]
                    next_section_title = list(next_section_articles[0].keys())[0] if next_section_articles else ''
                    next_section_index = all_text.find(next_section_title)
                else:
                    next_section_index = next_chapter_index

                for k, article_dict in enumerate(articles):
                    current_article_title = list(article_dict.keys())[0]

                    if k + 1 < len(articles):
                        next_article_title = list(articles[k+1].keys())[0]
                        next_article_index = all_text.find(next_article_title)
                    else:
                        next_article_index = next_section_index

                    current_article_index = all_text.find(current_article_title)

                    if current_article_index != -1 and next_article_index != -1:
                        raw_text = all_text[current_article_index:next_article_index].strip()
                        chunks = self.splitter.split_text(raw_text)

                        for chunk_text in chunks:
                            # 페이지 계산
                            page_index = -1
                            for p_idx, page in enumerate(doc):
                                if chunk_text[:50] in page.get_text():  # 단순 포함 여부로 찾음
                                    page_index = p_idx
                                    break

                            page_chunk_info.setdefault(page_index, 0)
                            i_chunk_on_page = page_chunk_info[page_index] + 1
                            page_chunk_info[page_index] += 1

                            chunk_with_title = f'[{self.legal_name}] [{chapter}] [{section}] {chunk_text}'
                            vectors.append(VectorMeta.model_validate({
                                'text': chunk_with_title,
                                'n_char': len(chunk_text),
                                'n_word': len(chunk_text.split()),
                                'i_page': page_index + 1,
                                'i_chunk_on_page': i_chunk_on_page,
                                'n_chunk_of_page': 0,  # 아래에서 채움
                                'i_chunk_on_doc': chunk_idx + 1,
                                'n_chunk_of_doc': 0,  # 아래에서 채움
                                'n_page': len(doc) + index,
                            }))
                            chunk_idx += 1

        # 최종 값 채우기 (n_chunk_of_doc, n_chunk_of_page)
        total_chunks = len(vectors)
        page_chunk_counts = {p+1 : 0 for p in page_chunk_info}
        for vector in vectors:
            vector.n_chunk_of_doc = total_chunks
            if vector.i_page is not None:
                page_chunk_counts[vector.i_page] += 1
            
        for vector in vectors:
            if vector.i_page is not None:
                vector.n_chunk_of_page = page_chunk_counts[vector.i_page]
                vector.i_page = vector.i_page + index
        return vectors
    
    def preprocess(self, file_path: str):
        documents: list[Document] = self.load_documents(file_path)
        self.documents = documents
        structure: dict[list] = self.split_documents(documents)
        self.structure = structure
        vectors: list[dict] = self.compose_vectors(structure, documents)
        return vectors
