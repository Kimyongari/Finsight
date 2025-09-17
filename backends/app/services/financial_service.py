from ..core.financial_searchengine.financial_statements_extractor import financial_statements_extractor
from ..core.financial_searchengine.dart_extractor import DartExtractor

class FinancialService:
    def __init__(self):
        self.extractor = financial_statements_extractor()
        self.dart_extractor = DartExtractor()

    def extract_financial_statements(self, corp_code: str) -> str:
        try:
            statement = {'statement' : self.extractor.extract_statement(corp_code = corp_code), 'success' : True}
        except Exception as e:
            statement = {'statemnet' : '', 'success' : False}
        
        return statement
    
    def search_corp_code_with_keyword(self, keyword:str):
        result = self.dart_extractor.get_corp_list_from_keyword(keyword)
        if result:
            return {'success' : True, 'data' : result}
        else:
            return {'success' : False, 'err_msg' : 'keyword와 일치하는 기업이 없습니다.'}
