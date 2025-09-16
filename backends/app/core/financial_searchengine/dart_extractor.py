
import os
import dart_fss as dart
from dotenv import load_dotenv
load_dotenv()
 
class DartExtractor:
    def __init__(self):
        dotenv_path = os.path.join(os.path.dirname(__file__), '../../.env')
        load_dotenv(dotenv_path=dotenv_path)
        self.api_key = os.getenv('OPENDART_API_KEY')
        if not self.api_key:
            raise ValueError("OPENDART_API_KEY가 .env 파일에 설정되지 않았습니다.")
        dart.set_api_key(api_key=self.api_key)

# stock_code : 6자 / corp_code : 8자
    def validate_corp_code(self, corp_code: str) -> str:
        """
        종목 코드를 사용하여 DART에서 기업 코드를 가져옵니다.
        """
        try:
            print(f"\n[DEBUG] Inside get_corp_code_by_stock_code")
            print(f"[DEBUG] Attempting to get corp_list for stock_code: {corp_code}")
            corp_list = dart.get_corp_list()
            company = corp_list.find_by_corp_code(corp_code)
            
            if company:
                print(f"[DEBUG] Company found: {company.corp_name}. Corp code: {company.corp_code}")
                return company.corp_code
            else:
                print(f"[DEBUG] Company not found for stock_code: {corp_code}")
                return None
        except Exception as e:
            print(f"\n[DEBUG] Exception in get_corp_code_by_stock_code: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_company_info(self, corp_code: str) -> dict:
        """
        기업 코드를 사용하여 DART에서 기업 개황 정보를 가져옵니다.
        """
        try:
            print("\n[DEBUG] Inside get_company_info")
            print(f"[DEBUG] Attempting to get corp_list for corp_code: {corp_code}")
            corp_list = dart.get_corp_list()
            company = corp_list.find_by_corp_code(corp_code)
            
            if company is None:
                print(f"[DEBUG] Company not found for corp_code: {corp_code}")
                return {"status": "404", "message": "Company not found"}
            
            print(f"[DEBUG] Company found: {company.corp_name}. Fetching profile...")
            company.load()
            print(f"[DEBUG] Profile fetched for {company.corp_name}.")

            return {
                "status": "000",
                "message": "정상",
                "corp_code": getattr(company, 'corp_code', ''),
                "corp_name": getattr(company, 'corp_name', ''),
                "corp_name_eng": getattr(company, 'corp_name_eng', ''),
                "stock_name": getattr(company, 'stock_name', ''),
                "stock_code": getattr(company, 'stock_code', ''),
                "ceo_nm": getattr(company, 'ceo_nm', ''),
                "corp_cls": getattr(company, 'corp_cls', ''),
                "jurir_no": getattr(company, 'jurir_no', ''),
                "bizr_no": getattr(company, 'bizr_no', ''),
                "adres": getattr(company, 'adres', ''),
                "hm_url": getattr(company, 'hm_url', ''),
                "ir_url": getattr(company, 'ir_url', ''),
                "phn_no": getattr(company, 'phn_no', ''),
                "fax_no": getattr(company, 'fax_no', ''),
                "induty_code": getattr(company, 'induty_code', ''),
                "est_dt": getattr(company, 'est_dt', ''),
                "acc_mt": getattr(company, 'acc_mt', '')
            }
        except Exception as e:
            print(f"\n[DEBUG] Exception in get_company_info: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "500", "message": str(e)}
