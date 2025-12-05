"""
该类用于实现简历打分+优化功能
"""
import time
from warnings import catch_warnings

import json
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed

from redis_client import RedisClient
from logger import get_logger

from LLMs.KimiUser import KimiUser
# from LLMs.deepseekUser import deepseekUser
from KnowledgeGraph.KgUser import KgUser
from KnowledgeSystem.KsUser import KsUser
from KnowledgeSystem.KsBuilder import KsBuilder
from Tools.DuckDuckGoUser import DuckDuckGoUser

log = get_logger(__name__)

kimi = KimiUser()
# ds = deepseekUser()
kg = KgUser()
ks_user = KsUser()
ks_builder = KsBuilder()
ddg = DuckDuckGoUser()

class AIWorker:
    """AI任务处理工作进程"""

    def __init__(self):
        self.redis_client = RedisClient()
        log.info("AI工作进程启动")

    def _pdf_resume_clean(self, pdf:str, task_id:str)->str:
        # pdf_text = ds.deepseek_resume_clean(pdf)
        # pdf_text = "暂无简历文本"
        pdf_text = kimi.kimi_resume_clean(pdf)
        log.info(f"清洗简历成功。{task_id}")
        return pdf_text


    def _keyword_extract(self, job_name:str, job_description:str, more_info:str, pdf_text:str)->list[str]:
        # ks_keywords = ["暂无"]
        ks_keywords = kimi.kimi_ks_keyword_extract(
            f"岗位名称：{job_name}。岗位描述：{job_description}。其他信息：{more_info}。简历内容：{pdf_text}。")
        log.info(f"内容检索成功。关键词：{ks_keywords}")
        return ks_keywords


    def _ks_search(self, ks_keywords:list[str])->str:
        # ks_info = ["暂无"]
        ks_info = ks_user.search_similar_text(ks_keywords)
        log.info(f"知识库信息获取成功:{ks_info}")
        return "###".join(ks_info)


    def _kg_search(self, job_name:str)->str:
        # kg_info = "暂无"
        kg_info = ' '.join(kg.find_skill_txt(job_name))
        log.info(f"知识图谱信息获取成功:{kg_info}")
        return kg_info


    def _search_resume(self, keywords:list[str])->str:
        tools_reply_resume = "暂无"
        # tools_reply_resume = ddg.ddg_search_resume(keywords)
        log.info(f"简历相关内容搜索完成:{tools_reply_resume}")
        return tools_reply_resume


    def _search_else(self, job_name:str, job_description:str, more_info:str)->str:
        tools_reply_else = "暂无"
        # tools_reply_else = ddg.ddg_search_else([job_name, job_description, more_info])
        log.info(f"简历无关内容搜索完成:{tools_reply_else}")
        return tools_reply_else


    def process_resume_task(self, task_data: dict):
        """处理简历分析任务"""
        try:
            task_data_json = task_data[1]   # JSON格式。无法直接提取内容
            # 解析JSON字符串为字典
            task_data_dict = json.loads(task_data_json)

            task_id = task_data_dict["task_id"]
            task_info_dict = task_data_dict["task_info"]
            pdf = task_info_dict["pdf全部文本"]
            job_name = task_info_dict["岗位名称"]
            job_description = task_info_dict["岗位描述"]
            more_info = task_info_dict["其他信息"]
            user_request = task_info_dict["用户备注"]

            # time.sleep(15)
            # return self.redis_client.input_res(task_id, "测试回复###$$$简历文本$$$###：简历内容为空")

            # 并行处理：
            # 1 简历清洗-->1.1 内容检索关键词-->1.1.1 知识库检索
            #                               1.1.2 工具搜索（简历相关）
            # 2 知识图谱检索
            # 3 工具搜索（简历无关）
            with ThreadPoolExecutor(max_workers=6) as executor:
                # 提交所有并行任务
                future_clean = executor.submit(self._pdf_resume_clean, pdf, task_id)
                future_kg = executor.submit(self._kg_search, job_name)
                future_else_search = executor.submit(self._search_else,job_name, job_description, more_info)

                # 等待简历清洗任务完成，准备内容检索关键词任务
                pdf_text = future_clean.result()
                future_keywords = executor.submit(self._keyword_extract, job_name, job_description,
                                                  more_info, pdf_text)

                # 等待内容检索关键词任务完成，准备知识库检索、工具搜索（简历相关）任务
                keywords = future_keywords.result()
                future_ks = executor.submit(self._ks_search, keywords)
                future_resume_search = executor.submit(self._search_resume, keywords)

                ks_info = future_ks.result()
                kg_info = future_kg.result()
                tools_reply_resume = future_resume_search.result()
                tools_reply_else = future_else_search.result()


            # 生成最终结果
            # res = "暂无"
            res = kimi.getKimiResponses(pdf_text, job_name+"  "+job_description, ks_info, kg_info,
                                        tools_reply_resume+"###"+tools_reply_else, user_request, more_info)
            res = res+"###$$$简历文本$$$###："+ pdf_text
            log.info(f"简历任务处理完成。{task_id}")
            self.redis_client.input_res(task_id, res)
            log.info(f"简历任务上传完成。{task_id}")
            log.info(f"简历任务上传完成。{res}")
            return res

        except Exception as e:
            log.error(f"处理简历任务失败。{task_data[1]["task_id"]}，错误信息：{e}")
            return {"task_id": task_data[1]["task_id"], "status": "failed", "error": str(e)}

    def start_working(self):
        """开始处理任务"""
        log.info("工作进程开始运行...")
        while True:
            try:
                resume_task = self.redis_client.popQueue_RO(timeout=5)
                if resume_task:
                    result = self.process_resume_task(resume_task)
            except KeyboardInterrupt:
                log.info("工作进程被用户中断")
                break
            except Exception as e:
                log.error(f"工作进程错误: {e}")
                time.sleep(1)  # 出错后休息1秒


def main():
    worker = AIWorker()
    worker.start_working()

if __name__ == "__main__":
    main()