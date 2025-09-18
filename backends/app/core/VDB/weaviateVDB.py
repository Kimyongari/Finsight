import weaviate
import os
from urllib.parse import urlparse
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.classes.config import Property, DataType
from .navercloud_embedding import NaverCloudEmbeddings
from tqdm import tqdm

# 네이버클라우드 임베딩 모델 (bge-m3) 모델을 활용하여 Weaviate VDB의 CRUD 및 검색을 수행합니다.
class VectorDB:
    def __init__(self,
                 url = None, http_port = None, grpc_port = None):
        self.client = None
        self.collection = None
        try:
            weaviate_url = os.getenv("WEAVIATE_URL")
            if weaviate_url:
                parsed_url = urlparse(weaviate_url)
                http_host = parsed_url.hostname
                http_port = parsed_url.port
                
                # Assuming gRPC port is 50051 as per docker-compose
                grpc_port = 50051 

                self.client = weaviate.connect_to_custom(
                    http_host=http_host,
                    http_port=http_port,
                    http_secure=False,
                    grpc_host=http_host,
                    grpc_port=grpc_port,
                    grpc_secure=False,
                    additional_config=AdditionalConfig(timeout=Timeout(init=30)) # Increase timeout
                )
                if self.client.is_ready():
                    print(f'weaviate에 {weaviate_url}로 접속하였습니다.')
            # This case is for external connection
            elif url and http_port and grpc_port:
                self.client = weaviate.connect_to_custom(
                                http_host=url,
                                http_port=http_port,
                                http_secure=False,
                                grpc_host=url,
                                grpc_port=grpc_port,
                                grpc_secure=False,
                            )
                if self.client and self.client.is_ready():
                    print('weaviate 외부 접속하였습니다.')

            else:
                # Fallback to local if WEAVIATE_URL is not set
                self.client  = weaviate.connect_to_local(
                                port=8080,  # REST
                                grpc_port=50051,  # gRPC
                                additional_config=AdditionalConfig(timeout=Timeout(init=10))
                            )
                if self.client.is_ready():
                    print('weaviate 로컬 접속하였습니다.')

        except Exception as e:
            print(f'weaviate 접속에 실패했습니다. 서버 혹은 접속정보를 확인해 주세요. 에러: {e}')
        self.embedding_model = NaverCloudEmbeddings()
        test = self.embedding_model.embed_query('안녕?')
        if 'err_msg' in test:
            print('네이버클라우드 임베딩 모델 호출에 실패했습니다. 접속정보를 확인하세요.')
            print('err_msg:', test['err_msg'])
            raise Exception
        
    def check(self, name:str):
        collection = self.client.collections.get(name)
        if collection.exists():
            self.collection = collection
            return True
        else:
            return False

# VDB에 존재하는 collection을 모두 삭제합니다. (사용주의)
    def reset(self):
        self.client.collections.delete_all()
        print('erased all collections in VDB.')

# VDB에 존재하는 모든 collection의 이름을 조회합니다.
    def show_collection(self):
        return self.client.collections.list_all()
        
# 이후 사용할 collection을 세팅합니다.
    def set_collection(self, name: str):
        collection = self.client.collections.get(name)
        if collection.exists():
            self.collection = collection
            print(f'{name} collection configured successfully.')
        else:
            raise Exception(f"{name} collection don't exist in weaviate db.")

# collection 을 제작합니다. 외부 벡터를 저장하는 기능만 있으며, 이후 필요시 내부 vector_config도 입력받도록 개발하는 것이 추가될 수 있습니다.
    def create_collection(self, properties:list[Property], name:str):
        if self.client.collections.exists(name):
            print(f'{name} collection already exists.')
            
        else:
            self.client.collections.create(
                name,
                properties = properties
            )
            print(f'{name} collection created.')

# colleciton 을 삭제합니다.
    def delete_collection(self, name: str):
        if self.client.collections.exists(name):
            self.client.collections.delete(
                name
            )
            print(f'{name} collection deleted.')
        else:
            raise Exception(f"{name} collection don't exist in weaviate db.")

# 특정 collection에 프로퍼티를 추가합니다.
    def add_property(self, properties:list[Property]):

        collection = self.collection
        if getattr(self.collection, 'exists', None):  
            if collection.exists():
                collection.config.add_property(properties) 
        else:
            raise ValueError("Collection이 지정되지 않았습니다. set_collection()으로 먼저 설정하세요.")

# 세팅 된 collection에 존재하는 프로퍼티를 전부 출력합니다.
    def show_properties(self, name = None):
        if name:
            self.set_collection(name = name)
            collection = self.collection
        else:
            collection = self.collection
        if getattr(self.collection, 'exists', None):  
            if collection.exists():
                properties = self.client.collections.list_all()[collection.data.name].properties
                for property in properties:
                    print(property)
        else:
            raise ValueError("Collection이 지정되지 않았습니다. set_collection()으로 먼저 설정하세요.")

# 특정 collection에 vector와 함께 object를 추가합니다.
    def add_object(self, object:dict):

        if 'text' not in object:
            raise Exception('입력한 object에 text 키가 존재하지 않습니다.')
        else:
            collection = self.collection
            if getattr(self.collection, 'exists', None):  
                if collection.exists():
                    vector = self.embedding_model.embed_query(object['text'])['embedding']
                    collection.data.insert(
                        properties=object,
                        vector = vector
                    )  
            else:
                raise ValueError("Collection이 지정되지 않았습니다. set_collection()으로 먼저 설정하세요.")
    
            
# 특정 collection에 vector와 함께 다수의 object를 추가합니다.
    def add_objects(self, objects:list[dict]):
        collection = self.collection
        if getattr(self.collection, 'exists', None):        
            if collection.exists():
                with collection.batch.fixed_size(batch_size=32) as batch:
                    for object in tqdm(objects, desc = '적재중..'):
                        # The model provider integration will automatically vectorize the object
                        vector = self.embedding_model.embed_query(object['text'])['embedding']
                        batch.add_object(
                            properties=object,
                            vector=vector  # Optionally provide a pre-obtained vector
                        )
                        if batch.number_errors > 10:
                            print("Batch import stopped due to excessive errors.")
                            break
                        if batch.number_errors != 0:
                            print('몇몇 chunk가 적재에 실패하였지만 그 수가 10을 넘지 않아 제외하고 적재되었습니다.')
        else:
            raise ValueError("Collection이 지정되지 않았습니다. set_collection()으로 먼저 설정하세요.")

# BM25 Search
    def query_bm25(self, query: str, topk: int = 4, fields: list = None):
        if getattr(self.collection, 'exists', None):     
            query_fields = fields if fields else ['text']
            results = self.collection.query.bm25(
                query=query,
                query_properties=query_fields,
                limit=topk
            )
            results = [i.properties for i in results.objects]
        else:
            raise ValueError("Collection이 지정되지 않았습니다. set_collection()으로 먼저 설정하세요.")

        return results
    
# Dense Search
    def query_dense(self, query: str, topk: int = 4, fields: list = None):
        if getattr(self.collection, 'exists', None):
            vector = self.embedding_model.embed_query(query)['embedding']
            results = self.collection.query.near_vector(
                near_vector = vector,
                limit = topk,
                )
            results = [i.properties for i in results.objects]
        else:
            raise ValueError("Collection이 지정되지 않았습니다. set_collection()으로 먼저 설정하세요.")
        return results
        
# BM25 + Dense Search (alpha)
# alpha 1 means pure vector search
# alpha 0 means pure keyword search
    def query_hybrid(self, query: str, topk: int = 4, fields: list = None, alpha:float = 0.5):
        if getattr(self.collection, 'exists', None):
            query_fields = fields if fields else ['text']
            vector = self.embedding_model.embed_query(query)['embedding']
            results = self.collection.query.hybrid(
                query = query,
                vector = vector,
                alpha = alpha,
                query_properties = query_fields,
                limit = topk
            )
            results = [i.properties for i in results.objects]
        else:
            raise ValueError("Collection이 지정되지 않았습니다. set_collection()으로 먼저 설정하세요.")
        return results