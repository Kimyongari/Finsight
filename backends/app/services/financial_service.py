from ..core.financial_searchengine.financial_statements_extractor import financial_statements_extractor

class FinancialService:
    def __init__(self):
        self.extractor = financial_statements_extractor()

    def extract_financial_statements(self, corp_code: str) -> str:
        try:
            statement = {'statement' : self.extractor.extract_statement(corp_code = corp_code), 'success' : True}
        except Exception as e:
            statement = {'statemnet' : '', 'success' : False}
        
        return statement
