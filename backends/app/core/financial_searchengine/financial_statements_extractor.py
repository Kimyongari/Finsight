import OpenDartReader
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup, Tag
import pandas as pd
from ..llm.llm import Midm
from bs4 import BeautifulSoup


load_dotenv()

class financial_statements_extractor:
    def __init__(self):
        self.dart = OpenDartReader(api_key = os.getenv('OPENDART_API_KEY'))
        self.midm = Midm()
    def url2html(self, url: str) -> str:
        """
        URL을 입력받아 HTML 내용을 가져온 후 BeautifulSoup 객체로 변환합니다.

        Args:
            url (str): 분석할 웹 페이지의 URL.

        Returns:
            BeautifulSoup | None: 성공 시 파싱된 BeautifulSoup 객체, 실패 시 None.
        """
        try:
            # 지정된 URL에 HTTP GET 요청을 보냄 (타임아웃 10초)
            response = requests.get(url, timeout=10)
            
            # 200 OK 상태 코드가 아닐 경우 예외를 발생시켜 에러 처리
            response.raise_for_status()

            # 응답 받은 HTML 텍스트를 BeautifulSoup 객체로 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            
            return str(soup)

        except requests.exceptions.RequestException as e:
            # 네트워크 오류, 타임아웃, 잘못된 URL 등의 요청 관련 에러 처리
            print(f"Error fetching URL '{url}': {e}")
            return None
        except Exception as e:
            # 기타 예외 처리
            print(f"An unexpected error occurred: {e}")
            return None
        
        
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        # 비어있으면 그대로 반환
        if df.empty:
            return df

        # 1. 컬럼 문자열화
        df.columns = df.columns.map(str)

        # 2. 멀티헤더 처리
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [
                ' '.join([str(i) for i in col if 'Unnamed' not in str(i)]).strip()
                for col in df.columns.values
            ]
        
        # 3. 일반 컬럼도 Unnamed 제거
        df.columns = [c.replace('Unnamed: 0', '').strip() for c in df.columns]

        # 4. 첫 컬럼명이 비어있으면 '구분'으로 변경
        if df.columns[0] == '':
            df.rename(columns={df.columns[0]: '구분'}, inplace=True)

        # 5. NaN → 빈 문자열
        df = df.fillna('')

        # 💡 항상 DataFrame을 반환하도록 수정
        return df
    def extract_main_content(self, html_content: str) -> str:
        """
        HTML 전체에서 <body> 내부의 실제 콘텐츠만 추출하는 함수
        """
        # HTML 파싱
        soup = BeautifulSoup(html_content, "lxml")

        # <body> 태그 찾기
        body = soup.find("body")
        if not body:
            raise ValueError("HTML에 <body> 태그가 없습니다.")

        # <body> 내부의 컨텐츠만 가져오기 (HTML 문자열로 변환)
        main_content = "".join(str(child) for child in body.contents if child.name or child.strip())

        return main_content.strip()
    def _extract_statements(self, url, mode = 'html'):
        html = self.url2html(url)
        if mode == 'html':
            financial_statement = self.extract_main_content(html)
            return financial_statement
        elif mode == 'markdown':
            dfs = pd.read_html(html)
            dfs_markdown = []
            for df in dfs:
                if isinstance(df, pd.DataFrame):
                    # 1. 데이터프레임을 먼저 정리
                    cleaned_df = self.clean_dataframe(df)

                    # 2. 정리된 데이터프레임의 컬럼 수에 따라 분기
                    if cleaned_df.shape[1] == 1:
                        # 컬럼이 1개면 직접 문자열로 변환
                        content = '\n\n'.join([str(item) for sublist in cleaned_df.values.tolist() for item in sublist])
                        dfs_markdown.append(content)
                    else:
                        # 컬럼이 여러 개면 to_markdown 호출
                        dfs_markdown.append(cleaned_df.to_markdown(index=False))
                else:
                    # DataFrame이 아닌 다른 타입은 그대로 추가
                    dfs_markdown.append(df)

            # financial_statement 합치는 코드는 동일
            financial_statement = ''
            for item in dfs_markdown:
                financial_statement += '\n' + str(item) + '\n' # str(item)으로 안정성 추가

            return financial_statement
        else:
            raise ValueError("mode가 설정되지 않았습니다. html, markdown 중 하나를 선택하세요.")
    
    # 00266961
    def get_recent_report(self, corp_code: str) -> str:
        recent_rcept_no = None
        try:
            recent_rcept_no= self.dart.list(corp_code, start='1999-01-01', kind='A').iloc[0]['rcept_no']
        except Exception as e:
            print('입력하신 기업 코드로 검색된 리포트 정보가 없습니다. 기업 코드를 다시 확인해 주세요.')
            return None
        
        return recent_rcept_no
    
    def infer_statement_idx(self,rcept_no:str) -> int:
        system_prompt = """당신은 재무제표 인덱스 검색가입니다. 주어진 목차를 바탕으로 재무제표가 몇번에 해당하는지 숫자를 말하세요. 
        [주의사항]
        1. 연결 재무제표, 연결 재무제표 주석, 재무제표 주석 등이 아닌 '재무제표' 라는 이름을 갖는 인덱스만 찾아야 합니다.
        2. 다른 말은 절대 하지 말고 오로지 숫자만 말하세요. 예시:20
        3. 인덱스를 찾을 수 없을 경우, '-1'만 출력하세요."""
         
        idxs =  str({i : value for i, value in enumerate(self.dart.sub_docs(rcept_no)['title'].values.tolist())})
        idx = self.midm.call(system_prompt=system_prompt, user_input=idxs)
        
        self.reports = self.dart.sub_docs(rcept_no)
        self.idx = idx
        try:
            idx = int(idx)
        except Exception as e:
            print('idx 추출 실패. -1 로 return 합니다. 받은 input:', idx)
            idx = -1
        return idx
        

    def get_statemnets_url(self, idx:int, rcept_no) -> str:
        urls = self.dart.sub_docs(rcept_no)

        statement_url = urls.iloc[idx]['url']
        return statement_url

    def extract_statement(self, corp_code:str, mode = 'html')->str:
        recent_rcept_no = self.get_recent_report(corp_code = corp_code)
        statement_idx = self.infer_statement_idx(rcept_no = recent_rcept_no)
        statement_url = self.get_statemnets_url(idx = statement_idx, rcept_no = recent_rcept_no)
        financial_statement = self._extract_statements(url = statement_url, mode = mode)
        return financial_statement
    