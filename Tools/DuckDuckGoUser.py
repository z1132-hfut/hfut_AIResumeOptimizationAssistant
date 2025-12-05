"""
用于使用搜索工具DuckDuckGo
"""
from typing import List
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper


from logger import get_logger

log = get_logger()


class DuckDuckGoUser:
    def __init__(self,
        max_results: int = 3,  # 每个关键词返回最多结果数（免费版建议3-5条）
        timeout: int = 10,    # 搜索超时时间（秒）
        region: str = "cn-en"  # 搜索区域（cn-en=中英文名，us-en=英文，cn-zh=纯中文）
    ):
        """
        初始化DuckDuckGo搜索工具
        :param max_results: 每个关键词返回的最大结果数
        :param region: 搜索区域配置（影响结果地域相关性）
        """
        # 配置DuckDuckGo搜索参数
        self.search_wrapper = DuckDuckGoSearchAPIWrapper(
            max_results=max_results,
            region=region,
            safesearch="off"  # 关闭安全搜索（避免过滤有效信息，可改为"moderate"增强过滤）
        )
        # 初始化搜索工具
        self.search_tool = DuckDuckGoSearchRun(api_wrapper=self.search_wrapper)

    def _batch_search(self, keywords: List[str]) -> str:
        """
        私有批量搜索核心方法：过滤空关键词 + 执行搜索 + 结果汇总去重
        :param keywords: 搜索关键词列表
        :return: 汇总后的搜索结果文本
        """
        # 过滤空关键词（避免无效请求）
        valid_keywords = [kw.strip() for kw in keywords if kw.strip()]
        if not valid_keywords:
            log.warning("未输入有效搜索关键词，返回空结果")
            return "未提供有效搜索关键词，无法获取结果"

        total_results = []
        for idx, keyword in enumerate(valid_keywords, 1):
            log.info(f"正在搜索第{idx}/{len(valid_keywords)}个关键词：{keyword}")
            try:
                # 执行单关键词搜索（返回简洁摘要结果）
                result = self.search_tool.run(keyword)
                if result.strip():
                    # 给每个关键词的结果添加标题，便于区分
                    formatted_result = f"### 关键词：{keyword}\n{result}\n"
                    total_results.append(formatted_result)
                else:
                    log.warning(f"关键词「{keyword}」未搜索到有效结果")
            except Exception as e:
                log.error(f"关键词「{keyword}」搜索失败：{str(e)}", exc_info=True)
                total_results.append(f"### 关键词：{keyword}\n搜索失败：{str(e)}\n")

        # 去重（避免不同关键词返回重复内容）
        unique_results = list(dict.fromkeys(total_results))  # 保持顺序去重
        # 合并所有结果
        final_result = "\n".join(unique_results) if unique_results else "所有关键词均未搜索到有效结果"
        log.info(f"搜索完成，共获取{len(unique_results)}个有效关键词结果")
        return final_result


    def ddg_search_resume(self, keywords:List[str])->str:
        """
        用于检索简历相关内容
        :return:汇总后的搜索结果文本
        """
        log.info("开始执行简历相关内容搜索")
        return self._batch_search(keywords)


    def ddg_search_else(self, else_text:List[str])->str:
        """
        用于检索简历无关内容
        :return:汇总后的搜索结果文本
        """
        log.info("开始执行非简历相关内容搜索")
        return self._batch_search(else_text)



if __name__ == "__main__":
    ddg = DuckDuckGoUser()
    ddg1 = ddg.ddg_search_resume(["国有企业 校招招聘偏好","高新技术行业 校招招聘偏好","挑战杯 赛事信息","发明专利 企业招聘含金量与价值"])
    ddg2 = ddg.ddg_search_else(["AI应用开发工程师 岗位能力需求","中鼎科技 相关信息",""])

    print(ddg1)
    print(ddg2)
