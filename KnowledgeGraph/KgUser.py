"""
使用知识图谱
"""
import os
from typing import Any, Dict, List

from neo4j import GraphDatabase
from logger import get_logger

log = get_logger(__name__)

class KgUser():
    def __init__(self):
        URI = "neo4j+s://e2937e0c.databases.neo4j.io"
        AUTH = ("neo4j", "scZxmOTV9Hr8jiRIZbziE1NKtJjJGMQs_LSfroDXMfM")
        try:
            self.driver = GraphDatabase.driver(URI, auth=AUTH)
            self.driver.verify_connectivity()
            log.info("Aura Neo4j数据库连接成功")
        except Exception as e:
            log.error(f"Aura Neo4j数据库连接失败。{e}")

    def print_kg(self) -> Dict[str, List[str]]:
        """
        查询所有岗位及其对应的要求，返回结构化字典
        :return: 格式为 {"岗位1":["要求1","要求2"], "岗位2":["要求1","要求2"]} 的字典
        """
        # 优化Cypher：直接匹配职业节点和对应的要求节点，减少冗余返回
        records, summary, keys = self.driver.execute_query("""
            MATCH (p:职业)-[r:要求]->(req)
            RETURN p.`Property 1` AS job_name, req.`Property 1` AS requirement
            ORDER BY job_name;
            """,
            database_="neo4j"
            )

        # 初始化返回字典
        job_requirements: Dict[str, List[str]] = {}

        if not records:
            log.info("图数据库中暂无职业-要求数据")
            return job_requirements

        # 遍历结果，按岗位分组整理要求
        for record in records:
            job_name = record.get("job_name", "").strip()
            requirement = record.get("requirement", "").strip()

            # 过滤空值
            if not job_name or not requirement:
                continue

            # 岗位不存在则初始化列表，存在则追加要求
            if job_name not in job_requirements:
                job_requirements[job_name] = []
            # 避免重复添加相同要求
            if requirement not in job_requirements[job_name]:
                job_requirements[job_name].append(requirement)

        print(job_requirements.get("数据分析师"))
        return job_requirements

    def save_kg_to_txt(self, file_path: str = "kg_jobInfo.txt"):
        """
        保存原字典结构到txt（Python原生格式，可直接还原）
        :param file_path: 保存路径（默认同文件夹）
        """
        # 获取原结构结果
        kg_data = self.print_kg()
        # 确认文件路径（同文件夹）
        full_path = os.path.join(os.path.dirname(__file__), file_path)

        # 用repr保存字典（保持原结构，可直接eval解析）
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(repr(kg_data))  # 核心：保存字典的原生字符串表示
            log.info(f"原结构数据已保存到：{full_path}")
        except Exception as e:
            log.error(f"保存失败：{e}")

    @staticmethod
    def load_kg_from_txt(file_path: str = "kg_jobInfo.txt") -> Dict[str, List[str]]:
        """
        从txt读取并还原原字典结构（直接调用）
        :return: 与print_kg返回完全一致的字典
        """
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                # eval直接还原字典（与原结构完全一致）
                kg_data = eval(f.read())
            log.info(f"成功加载原结构数据，共{len(kg_data)}个岗位")
            return kg_data
        except FileNotFoundError:
            log.error(f"文件{full_path}不存在")
            return {}
        except Exception as e:
            log.error(f"加载失败：{e}")
            return {}


    def find_skill_Aura(self, job_name: str, flat_and_filter: bool = True) -> list[str]:
        """
        根据岗位名称查询能力要求。
        :param job_name: 岗位名称
        :param flat_and_filter: 是否进行拆分、统计和过滤（默认为False，保持原行为）
        :return: 技能要求列表
        """
        records, summary, keys = self.driver.execute_query("""
            MATCH (p:职业 {`Property 1`: $job_name})-[r:要求]->(req)
            RETURN req.`Property 1` AS skill_text;
            """,
            job_name=job_name,
            database_="neo4j",
            )
        # 提取"要求"属性的值
        result = []
        for record in records:
            result.append(record["skill_text"])

        # 如果不进行拆分过滤，直接返回原结果
        if not flat_and_filter:
            log.info(f"职业：{job_name}，查询返回 {len(result)} 条结果，耗时 {summary.result_available_after} 毫秒。")
            return result

        # 统计每个技能的出现次数
        skill_counter = {}  # 字典：去重+计数
        total_records = len(result)
        log.info(f"查询结果总数：{total_records}")

        for skill_group in result:
            if skill_group:
                # 按逗号拆分，去除空格
                skills = [s.strip() for s in skill_group.split(',')]
                # 对每个技能进行计数
                for skill in skills:
                    if skill:  # 确保非空
                        skill_counter[skill] = skill_counter.get(skill, 0) + 1

        if skill_counter:
            counts = list(skill_counter.values())
            counts.sort()  # 升序排序

            len_count = len(counts)
            log.info(f"拆分去重（重复值进行计数）后结果总数：{len_count}")
            log.info(f"全词汇出现次数：{counts}")

            # 根据结果总数计算分位数。
            if len_count < 20:
                index = int(len_count * 0.4)
            elif len_count < 50:
                index = int(len_count * 0.6)
            elif len_count < 100:
                index = int(len_count * 0.7)
            elif len_count < 200:
                index = int(len_count * 0.8)
            elif len_count < 400:
                index = int(len_count * 0.9)
            else:
                index = int(len_count * 0.95)

            threshold = counts[index] if index < len_count else counts[-1]  # 最小出现次数
            log.info(f"前百分位数索引：{index}")
            log.info(f"最小出现次数：{threshold}")

            # 过滤
            filtered_skills = [
                skill for skill, count in skill_counter.items()
                if count >= threshold
            ]
            log.info(f"过滤后结果总数：{len(filtered_skills)}")

            # 按出现次数降序排序
            sorted_skills = sorted(
                filtered_skills,
                key=lambda x: skill_counter[x],
                reverse=True
            )
            # log.info(f"过滤+根据次数倒序排序后的结果：{sorted_skills}")

            log.info(f"查询耗时：{summary.result_available_after} 毫秒")

            return sorted_skills
        else:
            log.info(f"职业：{job_name}，未找到有效技能")
            return []


    def find_skill_txt(self, job_name: str) -> list[str]:
        """
        根据岗位名称查询能力要求。
        :param job_name: 岗位名称
        :return: 技能要求列表
        """
        loaded_data = KgUser.load_kg_from_txt()
        result = loaded_data.get("数据分析师")
        # 提取"要求"属性的值
        # result = []
        # for record in records:
        #     result.append(record["skill_text"])

        # 统计每个技能的出现次数
        skill_counter = {}  # 字典：去重+计数
        total_records = len(result)
        log.info(f"查询结果总数：{total_records}")

        for skill_group in result:
            if skill_group:
                # 按逗号拆分，去除空格
                skills = [s.strip() for s in skill_group.split(',')]
                # 对每个技能进行计数
                for skill in skills:
                    if skill:  # 确保非空
                        skill_counter[skill] = skill_counter.get(skill, 0) + 1

        if skill_counter:
            counts = list(skill_counter.values())
            counts.sort()  # 升序排序

            len_count = len(counts)
            log.info(f"拆分去重（重复值进行计数）后结果总数：{len_count}")
            log.info(f"全词汇出现次数：{counts}")

            # 根据结果总数计算分位数。
            if len_count < 20:
                index = int(len_count * 0.4)
            elif len_count < 50:
                index = int(len_count * 0.6)
            elif len_count < 100:
                index = int(len_count * 0.7)
            elif len_count < 200:
                index = int(len_count * 0.8)
            elif len_count < 400:
                index = int(len_count * 0.9)
            else:
                index = int(len_count * 0.95)

            threshold = counts[index] if index < len_count else counts[-1]  # 最小出现次数
            log.info(f"前百分位数索引：{index}")
            log.info(f"最小出现次数：{threshold}")

            # 过滤
            filtered_skills = [
                skill for skill, count in skill_counter.items()
                if count >= threshold
            ]
            log.info(f"过滤后结果总数：{len(filtered_skills)}")

            # 按出现次数降序排序
            sorted_skills = sorted(
                filtered_skills,
                key=lambda x: skill_counter[x],
                reverse=True
            )
            # log.info(f"过滤+根据次数倒序排序后的结果：{sorted_skills}")

            return sorted_skills
        else:
            log.info(f"职业：{job_name}，未找到有效技能")
            return []

if __name__ == "__main__":
    kg = KgUser()
    # kg.print_kg()
    # print(kg.find_skill("AI应用开发工程师"))
    # print(kg.find_skill("Java开发工程师"))
    print(kg.find_skill_Aura("数据分析师"))
    print(kg.find_skill_txt("数据分析师"))
    # kg.save_kg_to_txt()

    # 步骤2：后期调用（直接还原字典，结构与print_kg完全一致）
    # loaded_data = KgUser.load_kg_from_txt()
    # 直接调用，用法和原print_kg结果完全一样
    # print(loaded_data.get("数据分析师"))