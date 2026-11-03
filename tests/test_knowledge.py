import json
from io import StringIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).parents[1] / 'scripts'))
import studio_git as module

APP='11111111-1111-4111-8111-111111111111'
RECORD='22222222-2222-4222-8222-222222222222'
class KnowledgeTests(unittest.TestCase):
    def call(self,arguments):
        output=StringIO()
        with patch.object(sys,'argv',['studio_git.py',*arguments]), patch.object(module,'ensure_helper_runtime'), patch.object(sys,'stdout',output), patch.object(module,'mcp_call',return_value={'records':[]}) as request:
            code=module.main()
        return code,request,output.getvalue()

    def test_search_uses_selected_app_shared_authorization_and_pagination(self):
        code,request,output=self.call(['knowledge-search','--project-id',APP,'--query','work orders billing','--offset','20'])
        self.assertEqual(code,0)
        request.assert_called_once_with('search_app_knowledge',{'project_id':APP,'query':'work orders billing','offset':20})
        self.assertEqual(json.loads(output),{'records':[]})

    def test_get_binds_record_and_application_without_a_mutation(self):
        code,request,_=self.call(['knowledge-get','--project-id',APP,'--knowledge-id',RECORD])
        self.assertEqual(code,0)
        request.assert_called_once_with('get_app_knowledge',{'project_id':APP,'knowledge_id':RECORD})

    def test_suite_discovery_stays_bound_to_selected_app(self):
        code,request,_=self.call(['knowledge-search','--project-id',APP,'--knowledge-scope','suite'])
        self.assertEqual(code,0)
        request.assert_called_once_with('search_app_knowledge',{'project_id':APP,'query':'','offset':0,'scope':'suite'})

    def test_invalid_inputs_do_not_call_studio(self):
        for args in [ ['knowledge-search','--project-id',APP,'--offset','-1'], ['knowledge-search','--project-id',APP,'--query','x'*301], ['knowledge-get','--project-id',APP,'--knowledge-id','bad'] ]:
            with patch.object(sys,'stderr',StringIO()):
                code,request,_=self.call(args)
            self.assertNotEqual(code,0)
            request.assert_not_called()

if __name__=='__main__':unittest.main()
