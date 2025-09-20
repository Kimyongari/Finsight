from ..core.VDB.weaviateVDB import VectorDB
from ..core.Preprocessor.preprocessor import DocumentProcessor
from weaviate.classes.config import Property, DataType
from ..core.llm.llm import Midm
from glob import glob
from weaviate.classes.query import Filter
import time

class VDBService:
    def __init__(self, url=None, http_port=None, grpc_port=None):
        self.vdb = VectorDB(url=url, http_port=http_port, grpc_port=grpc_port)
        if 'LegalDB' in self.vdb.show_collection():
            self.vdb.set_collection('LegalDB')
        else:
            properties=[
                Property(name="text", data_type=DataType.TEXT),
                Property(name="n_char", data_type=DataType.INT),
                Property(name="n_word", data_type=DataType.INT),
                Property(name="i_page", data_type=DataType.INT),
                Property(name="i_chunk_on_page", data_type=DataType.INT),
                Property(name="n_chunk_of_page", data_type=DataType.INT),
                Property(name="i_chunk_on_doc", data_type=DataType.INT),
                Property(name="n_chunk_of_doc", data_type=DataType.INT),
                Property(name="n_page", data_type=DataType.INT),
                Property(name="name", data_type=DataType.TEXT),
                Property(name="file_path", data_type=DataType.TEXT),
                Property(name="file_name", data_type=DataType.TEXT)
            ]
            self.vdb.create_collection(name = 'LegalDB', properties=properties)
            self.vdb.set_collection('LegalDB')

    def initialize(self):
        try:

            paths = glob('./pdfs/*.pdf')
            files = [path.split('/')[-1] for path in paths]
            self.vdb.reset()
            self.__init__()
            for file_name in files:
                response = self.register(file_name = file_name)
                if response['success']:
                    continue
                else:
                    print(file_name, '적재 중 오류 발생', response['err_msg'])
            return {'success' : True, 'files' : paths}
        
        except Exception as e:
            print('Error during initialization:', str(e))
            return {'success' : False, 'err_msg' : str(e)}
        
    def register(self, file_name):
        path = f'./pdfs/{file_name}'
        try:
            processor = DocumentProcessor()
            chunks = processor.preprocess(file_path = path)
            if self.vdb.check(name = 'LegalDB'):
                objects = [{'text' : chunk.text,
                            'n_char' : chunk.n_char,
                            'n_word' : chunk.n_word,
                            'i_page' : chunk.i_page,
                            'i_chunk_on_page' : chunk.i_chunk_on_page,
                            'n_chunk_of_page' : chunk.n_chunk_of_page,
                            'i_chunk_on_doc' : chunk.i_chunk_on_doc,
                            'n_chunk_of_doc' : chunk.n_chunk_of_doc,
                            'n_page' : chunk.n_page,
                            'name' : chunk.name,
                            'file_path' : chunk.file_path,
                             'file_name' : chunk.file_name } for chunk in chunks]
                self.vdb.add_objects(objects = objects)
                return {'success' : True}
            else:
                return {'success' : False}
    
        except Exception as e:
            print('Error during initialization:', str(e))
            return {'success' : False, 'err_msg' : str(e)}
        
    def reset(self):
        try:        
            self.vdb.reset()
            return {'success': True}
        except Exception as e:
            return {'success' : False, 'err_msg' : f'reset에 실패하였습니다. 오류 : {e}'}
        
    
    def show_collections(self):
        return self.vdb.show_collection()
    
    def set_collection(self, name:str):
        try:
            self.vdb.set_collection(name)
            return {'success': True}
        except Exception as e:
            return {'success' : False, 'err_msg' : str(e)}
        
    def show_files_in_collection(self):
        try:
            unique_file_name_and_chunk = self.vdb.show_files_in_collection()
            return {'success': True, 'unique_file_name_and_chunk' : unique_file_name_and_chunk}
        except Exception as e:
            return {'success' : False, 'err_msg' : str(e)}
        
    def delete_objects_from_file_name(self, file_name):
        try:
            filter = Filter.by_property("file_name").equal(file_name)
            self.vdb.delete_obejcts(filter = filter)
            return {'success' : True}
        except Exception as e:
            return {'success' : False, 'err_msg' : str(e)}
        
