from ..core.financial_searchengine.financial_statements_extractor import financial_statements_extractor

class FinancialService:
    def __init__(self):
        self.extractor = financial_statements_extractor()

    def extract_financial_statements(self, corp_code: str) -> str:
        return self.extractor.extract_statement(corp_code = corp_code)