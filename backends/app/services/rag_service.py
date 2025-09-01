from ..core.VDB.weaviateVDB import VectorDB

class RagService:
    def __init__(self, url=None, http_port=None, grpc_port=None):
        self.vdb = VectorDB(url=url, http_port=http_port, grpc_port=grpc_port)

    def Retriever(self, query:str) -> dict:
        try:
            retrieved_documents = self.vdb.query_hybrid(query = query, topk = 4)
            return {'success' : True, 'data' : retrieved_documents}
        except Exception as e:
            return {'success' : False, 'err_msg' : str(e)}
    
    def show_collections(self):
        return self.vdb.show_collection()
    
    def set_collection(self, name:str):
        try:
            self.vdb.set_collection(name)
            return {'success': True}
        except Exception as e:
            return {'success' : False, 'err_msg' : str(e)}
